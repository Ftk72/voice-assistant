from datetime import UTC, datetime

import httpx

from app.config import Settings
from app.graph.base import CibleIntrouvable, CorrectionRefusee, GraphMemory
from app.graph.ontologie import TYPES_D_ENTITES
from app.schemas import (
    EpisodeIn,
    Fact,
    GrapheComplet,
    GraphEdge,
    GraphNeighborhood,
    NoeudGraphe,
    Provenance,
)


def _en_datetime(valeur):
    """Le driver Neo4j renvoie des `neo4j.time.DateTime`, que pydantic refuse :
    conversion vers le datetime natif (constaté au premier lancement réel, 2026-07-06)."""
    return valeur.to_native() if hasattr(valeur, "to_native") else valeur


def _provenance_depuis_description(description: str | None) -> Provenance:
    """Parse le `source_description` (« source:nom ») écrit par `add_episode` sur les
    nœuds `Episodic` en `Provenance`. Repli sur « conversation:inconnue » si absent ou
    vide, et sur la source « conversation » si la source annoncée n'est pas reconnue
    (garde-fou : un `Literal` pydantic ne doit jamais recevoir une valeur hors énum)."""
    description = description or "conversation:inconnue"
    prov_source, _, prov_name = description.partition(":")
    return Provenance(
        source=prov_source if prov_source in ("conversation", "document") else "conversation",
        name=prov_name or description,
    )


class GraphitiMemory(GraphMemory):
    """Adaptateur Graphiti + Neo4j (ADR 0005) — tourne au réel depuis début
    juillet 2026 (extraction, recherche, /viz, corrections du ticket 0029)."""

    def __init__(self, settings: Settings) -> None:
        self._embedder_base_url = settings.embedder_base_url
        try:
            from graphiti_core import Graphiti
            from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
            from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
            from graphiti_core.llm_client.config import LLMConfig
            from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
        except ImportError as error:
            raise RuntimeError(
                "graphiti-core n'est pas installé — lancer : uv sync --extra graphiti"
            ) from error

        from app.graph.francais import forcer_extraction_en_francais

        forcer_extraction_en_francais()

        self._graphiti = Graphiti(
            settings.neo4j_uri,
            settings.neo4j_user,
            settings.neo4j_password,
            # temperature=0 : le défaut de LLMConfig (1) rend l'extraction de nœuds
            # instable sur épisode court (diagnostic 2026-07-06 — « pétanque » extrait
            # 3/5 tirages seulement) ; l'extraction est une tâche déterministe.
            llm_client=OpenAIGenericClient(
                config=LLMConfig(
                    api_key="sk-local", base_url=settings.llm_base_url, temperature=0
                )
            ),
            embedder=OpenAIEmbedder(
                config=OpenAIEmbedderConfig(
                    api_key="sk-local", base_url=settings.embedder_base_url
                )
            ),
            # Sans cross_encoder explicite, Graphiti instancie un reranker OpenAI
            # par défaut : crash au démarrage (OPENAI_API_KEY absente) et appels
            # sortants vers api.openai.com — on le pointe sur le LLM local.
            cross_encoder=OpenAIRerankerClient(
                config=LLMConfig(api_key="sk-local", base_url=settings.llm_base_url)
            ),
        )

    async def initialize(self) -> None:
        """Crée les index et contraintes Neo4j de Graphiti (idempotent) — sans quoi
        chaque recherche échoue sur l'index fulltext `edge_name_and_fact` manquant."""
        await self._graphiti.build_indices_and_constraints()

    async def add_episode(self, episode: EpisodeIn) -> None:
        from graphiti_core.nodes import EpisodeType

        await self._graphiti.add_episode(
            name=episode.name,
            episode_body=episode.content,
            source=EpisodeType.message if episode.source == "conversation" else EpisodeType.text,
            source_description=f"{episode.source}:{episode.name}",
            reference_time=datetime.now(UTC),
            # Types explicites du domaine : sans eux, l'activité d'un épisode court
            # (« judo », « pétanque ») saute une fois sur deux → zéro fait (cf. ontologie.py).
            entity_types=TYPES_D_ENTITES,
        )

    async def search(self, query: str) -> list[Fact]:
        edges = await self._graphiti.search(query)

        # Provenance fine : on lit le `source_description` du premier épisode de
        # chaque arête (même convention que `neighborhood()`), via une seule requête
        # Cypher groupée plutôt qu'une par fait.
        episode_uuids = {
            edge.episodes[0] for edge in edges if getattr(edge, "episodes", None)
        }
        descriptions: dict[str, str | None] = {}
        if episode_uuids:
            records, _, _ = await self._graphiti.driver.execute_query(
                """
                MATCH (ep:Episodic) WHERE ep.uuid IN $uuids
                RETURN ep.uuid AS uuid, ep.source_description AS source_description
                """,
                uuids=sorted(episode_uuids),
            )
            descriptions = {record["uuid"]: record["source_description"] for record in records}

        facts = []
        for edge in edges:
            episode_uuid = edge.episodes[0] if getattr(edge, "episodes", None) else None
            description = descriptions.get(episode_uuid) if episode_uuid else None
            facts.append(
                Fact(
                    text=edge.fact,
                    provenance=_provenance_depuis_description(description),
                    valid_at=edge.valid_at,
                    invalid_at=edge.invalid_at,
                )
            )
        return facts

    async def neighborhood(self, entity: str, depth: int = 1) -> GraphNeighborhood:
        """Extension de proche en proche : une requête Cypher à un saut par niveau.
        La provenance vient du `source_description` (« source:nom ») écrit par
        add_episode sur le premier épisode de chaque fait."""
        nodes: set[str] = {entity}
        edges: list[GraphEdge] = []
        seen_edges: set[str] = set()
        frontier = {entity.lower()}
        visited: set[str] = set()
        for _ in range(depth):
            visited |= frontier
            records, _, _ = await self._graphiti.driver.execute_query(
                """
                MATCH (a:Entity)-[r:RELATES_TO]-(b:Entity)
                WHERE toLower(a.name) IN $names
                OPTIONAL MATCH (ep:Episodic) WHERE ep.uuid IN r.episodes
                RETURN a.name AS source, b.name AS target, r.uuid AS uuid,
                       r.fact AS text, r.valid_at AS valid_at, r.invalid_at AS invalid_at,
                       r.corrige_le AS corrige_le, r.corrige_geste AS corrige_geste,
                       collect(ep.source_description)[0] AS source_description
                """,
                names=sorted(frontier),
            )
            reached: set[str] = set()
            for record in records:
                nodes.update((record["source"], record["target"]))
                reached.update((record["source"].lower(), record["target"].lower()))
                if record["uuid"] in seen_edges:
                    continue
                seen_edges.add(record["uuid"])
                edges.append(
                    GraphEdge(
                        source=record["source"],
                        target=record["target"],
                        text=record["text"],
                        provenance=_provenance_depuis_description(record["source_description"]),
                        valid_at=_en_datetime(record["valid_at"]),
                        invalid_at=_en_datetime(record["invalid_at"]),
                        uuid=record["uuid"],
                        corrige_le=_en_datetime(record["corrige_le"]),
                        corrige_geste=record["corrige_geste"],
                    )
                )
            frontier = reached - visited
            if not frontier:
                break
        return GraphNeighborhood(center=entity, nodes=sorted(nodes), edges=edges)

    async def graphe_complet(self, limite: int = 500) -> GrapheComplet:
        """Deux requêtes Cypher : les nœuds les plus
        connectés (degré décroissant) jusqu'à `limite`, puis les arêtes qui les relient
        entre eux (même contrat que `neighborhood` — provenance et validité comprises,
        faits obsolètes marqués, jamais omis)."""
        total_records, _, _ = await self._graphiti.driver.execute_query(
            "MATCH (n:Entity) RETURN count(n) AS total"
        )
        total = total_records[0]["total"] if total_records else 0

        noeud_records, _, _ = await self._graphiti.driver.execute_query(
            """
            MATCH (n:Entity)
            OPTIONAL MATCH (n)-[r:RELATES_TO]-()
            WITH n, count(r) AS degre
            ORDER BY degre DESC, n.name ASC
            LIMIT $limite
            RETURN n.name AS nom, n.uuid AS uuid,
                   [l IN labels(n) WHERE l <> 'Entity'][0] AS type,
                   n.corrige_le AS corrige_le, n.corrige_geste AS corrige_geste,
                   n.nom_precedent AS nom_precedent, n.type_precedent AS type_precedent
            """,
            limite=limite,
        )
        noms = [record["nom"] for record in noeud_records]

        arete_records, _, _ = await self._graphiti.driver.execute_query(
            """
            MATCH (a:Entity)-[r:RELATES_TO]-(b:Entity)
            WHERE a.name IN $noms AND b.name IN $noms
            OPTIONAL MATCH (ep:Episodic) WHERE ep.uuid IN r.episodes
            RETURN a.name AS source, b.name AS target, r.uuid AS uuid,
                   r.fact AS text, r.valid_at AS valid_at, r.invalid_at AS invalid_at,
                   r.corrige_le AS corrige_le, r.corrige_geste AS corrige_geste,
                   collect(ep.source_description)[0] AS source_description
            """,
            noms=noms,
        )
        aretes: list[GraphEdge] = []
        vues: set[str] = set()
        for record in arete_records:
            if record["uuid"] in vues:
                continue
            vues.add(record["uuid"])
            aretes.append(
                GraphEdge(
                    source=record["source"],
                    target=record["target"],
                    text=record["text"],
                    provenance=_provenance_depuis_description(record["source_description"]),
                    valid_at=_en_datetime(record["valid_at"]),
                    invalid_at=_en_datetime(record["invalid_at"]),
                    uuid=record["uuid"],
                    corrige_le=_en_datetime(record["corrige_le"]),
                    corrige_geste=record["corrige_geste"],
                )
            )
        noeuds = [
            NoeudGraphe(
                nom=record["nom"],
                uuid=record["uuid"],
                type=record["type"],
                corrige_le=_en_datetime(record["corrige_le"]),
                corrige_geste=record["corrige_geste"],
                nom_precedent=record["nom_precedent"],
                type_precedent=record["type_precedent"],
            )
            for record in noeud_records
        ]
        return GrapheComplet(noeuds=noeuds, aretes=aretes, tronque=total > limite)

    async def corriger_type(self, uuid: str, type_: str) -> None:
        """Corrige le type (mal extrait) d'une entité — le type d'une entité est un
        label Neo4j autre que `Entity` (convention Graphiti, cf. ontologie.py).
        `type_` doit être une clé de `TYPES_D_ENTITES` (liste blanche) : seul cas
        où l'interpolation de label dans la chaîne Cypher est admise, les labels
        ne sont pas paramétrables en Cypher."""
        if type_ not in TYPES_D_ENTITES:
            raise ValueError(f"type hors liste blanche : {type_!r}")
        retirer_anciens_types = "\n".join(f"REMOVE n:{t}" for t in TYPES_D_ENTITES)
        records, _, _ = await self._graphiti.driver.execute_query(
            f"""
            MATCH (n:Entity {{uuid: $uuid}})
            WITH n, [l IN labels(n) WHERE l <> 'Entity'][0] AS ancien_type
            {retirer_anciens_types}
            SET n:{type_}
            SET n.labels = ['Entity', $type_],
                n.type_precedent = ancien_type,
                n.corrige_le = datetime(),
                n.corrige_geste = 'type'
            RETURN n.uuid AS uuid
            """,
            uuid=uuid,
            type_=type_,
        )
        if not records:
            raise CibleIntrouvable(uuid)

    async def renommer_entite(self, uuid: str, nom: str) -> None:
        """Renomme une entité mal orthographiée et recalcule son `name_embedding`
        (sinon `/search` continuerait de raisonner sur l'ancienne orthographe) :
        POST OpenAI-compat vers l'embedder local, puis écriture Cypher. Les
        textes des faits (`r.fact`) ne sont jamais touchés (citations
        historiques)."""
        async with httpx.AsyncClient() as client:
            reponse = await client.post(
                f"{self._embedder_base_url}/embeddings",
                json={"input": [nom], "model": "bge-m3"},
            )
            reponse.raise_for_status()
            embedding = reponse.json()["data"][0]["embedding"]

        records, _, _ = await self._graphiti.driver.execute_query(
            """
            MATCH (n:Entity {uuid: $uuid})
            SET n.nom_precedent = n.name,
                n.name = $nom,
                n.name_embedding = $embedding,
                n.corrige_le = datetime(),
                n.corrige_geste = 'renommage'
            RETURN n.uuid AS uuid
            """,
            uuid=uuid,
            nom=nom,
            embedding=embedding,
        )
        if not records:
            raise CibleIntrouvable(uuid)

    async def invalider_fait(self, uuid: str) -> None:
        """Invalide un fait faux dès son origine (erreur d'extraction, pas
        obsolescence) : `invalid_at = valid_at` (repli `created_at`). Jamais de
        suppression physique."""
        records, _, _ = await self._graphiti.driver.execute_query(
            """
            MATCH ()-[r:RELATES_TO {uuid: $uuid}]-()
            SET r.invalid_at = coalesce(r.valid_at, r.created_at),
                r.corrige_le = datetime(),
                r.corrige_geste = 'invalidation'
            RETURN r.uuid AS uuid
            """,
            uuid=uuid,
        )
        if not records:
            raise CibleIntrouvable(uuid)

    async def annuler_invalidation(self, uuid: str) -> None:
        """Annule une invalidation manuelle (remet `invalid_at` à null et efface la
        trace) — seulement si la trace porte `corrige_geste == 'invalidation'` :
        les invalidations apprises par Graphiti restent intouchables."""
        records, _, _ = await self._graphiti.driver.execute_query(
            """
            MATCH ()-[r:RELATES_TO {uuid: $uuid}]-()
            RETURN r.uuid AS uuid, r.corrige_geste AS corrige_geste
            """,
            uuid=uuid,
        )
        if not records:
            raise CibleIntrouvable(uuid)
        if records[0]["corrige_geste"] != "invalidation":
            raise CorrectionRefusee(uuid)
        await self._graphiti.driver.execute_query(
            """
            MATCH ()-[r:RELATES_TO {uuid: $uuid}]-()
            SET r.invalid_at = null,
                r.corrige_le = null,
                r.corrige_geste = null
            """,
            uuid=uuid,
        )

    async def forget(self, entity: str) -> int:
        """Suppression réelle des nœuds dont le nom correspond, et de leurs relations."""
        records, _, _ = await self._graphiti.driver.execute_query(
            """
            MATCH (n:Entity) WHERE toLower(n.name) CONTAINS toLower($entity)
            DETACH DELETE n
            RETURN count(n) AS deleted
            """,
            entity=entity,
        )
        return records[0]["deleted"] if records else 0
