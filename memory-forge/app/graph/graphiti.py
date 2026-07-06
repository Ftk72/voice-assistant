from datetime import UTC, datetime

from app.config import Settings
from app.graph.base import GraphMemory
from app.schemas import EpisodeIn, Fact, GraphEdge, GraphNeighborhood, Provenance


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
    """Adaptateur Graphiti + Neo4j (ADR 0005).

    ⚠️ Écrit d'après la documentation de graphiti-core, jamais exécuté (dépendances
    non installées à l'écriture — connexion lente). À valider au premier lancement
    réel, comme _RealChatterboxEngine côté voice-forge.
    """

    def __init__(self, settings: Settings) -> None:
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
            llm_client=OpenAIGenericClient(
                config=LLMConfig(api_key="sk-local", base_url=settings.llm_base_url)
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
                    )
                )
            frontier = reached - visited
            if not frontier:
                break
        return GraphNeighborhood(center=entity, nodes=sorted(nodes), edges=edges)

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
