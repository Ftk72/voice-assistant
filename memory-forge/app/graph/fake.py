import re
import uuid as uuid_lib
from datetime import UTC, datetime

from app.graph.base import CibleIntrouvable, CorrectionRefusee, GraphMemory
from app.schemas import (
    EpisodeIn,
    Fact,
    GrapheComplet,
    GraphEdge,
    GraphNeighborhood,
    NoeudGraphe,
    Provenance,
)

# Mots capitalisés en début de phrase à ne pas prendre pour des entités.
_STOPWORDS = {
    "le", "la", "les", "un", "une", "de", "du", "des", "il", "elle", "on",
    "au", "aux", "ce", "cette", "ces", "et", "mais", "ou", "dans", "pour",
    "sur", "avec", "sans", "chez",
}

# Espace de noms fixe pour des uuid déterministes (ticket wayfinder 0029) :
# même nom d'entité ou même fait → même uuid d'un appel à l'autre.
_NAMESPACE = uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, "memory-forge.fake")


def _uuid_noeud(nom: str) -> str:
    return str(uuid_lib.uuid5(_NAMESPACE, f"noeud:{nom.lower()}"))


def _uuid_arete(texte: str, indice: int) -> str:
    return str(uuid_lib.uuid5(_NAMESPACE, f"arete:{indice}:{texte}"))


class InMemoryGraph(GraphMemory):
    """Graphe factice pour les tests et le développement sans Neo4j/LLM :
    une phrase = un fait, recherche par simple inclusion de mots.

    Les entités sont ré-extraites du texte des faits à chaque appel (rien n'est
    stocké comme nœud à part) : les corrections (type, renommage) vivent donc
    dans deux registres à côté, appliqués à la construction du graphe — les
    uuid, eux, restent calculés depuis le nom ORIGINAL (celui qui apparaît dans
    le texte des faits), pour rester stables même après un renommage."""

    def __init__(self) -> None:
        self._facts: list[Fact] = []
        self._fact_uuids: dict[int, str] = {}  # id(fact) -> uuid stable
        # clé = nom original en minuscules
        self._corrections_noeuds: dict[str, dict] = {}
        self._corrections_aretes: dict[str, dict] = {}  # uuid de fait -> trace

    async def add_episode(self, episode: EpisodeIn) -> None:
        provenance = Provenance(source=episode.source, name=episode.name)
        for sentence in re.split(r"(?<=[.!?])\s+", episode.content):
            if sentence.strip():
                fait = Fact(
                    text=sentence.strip(),
                    provenance=provenance,
                    valid_at=datetime.now(UTC),
                )
                self._facts.append(fait)
                self._fact_uuids[id(fait)] = _uuid_arete(fait.text, len(self._facts) - 1)

    async def search(self, query: str) -> list[Fact]:
        words = query.lower().split()
        return [
            fact for fact in self._facts if any(word in fact.text.lower() for word in words)
        ]

    async def forget(self, entity: str) -> int:
        before = len(self._facts)
        gardes = []
        for fait in self._facts:
            if entity.lower() in fait.text.lower():
                self._fact_uuids.pop(id(fait), None)
            else:
                gardes.append(fait)
        self._facts = gardes
        return before - len(self._facts)

    async def neighborhood(self, entity: str, depth: int = 1) -> GraphNeighborhood:
        """Entités = mots capitalisés (naïf, assumé pour le factice) ; un fait relie
        entre elles toutes les entités de sa phrase."""
        nodes = {entity}
        edges: list[GraphEdge] = []
        frontier = {entity.lower()}
        visited: set[str] = set()
        seen_facts: set[int] = set()
        for _ in range(depth):
            visited |= frontier
            reached: set[str] = set()
            for fact in self._facts:
                if id(fact) in seen_facts or not any(
                    name in fact.text.lower() for name in frontier
                ):
                    continue
                seen_facts.add(id(fact))
                entities = _entities(fact.text) or [entity]
                nodes.update(self._nom_actuel(e) for e in entities)
                reached.update(e.lower() for e in entities)
                source = entities[0]
                for target in entities[1:] or [source]:
                    edges.append(self._arete_graphe(fact, source, target))
            frontier = reached - visited
            if not frontier:
                break
        return GraphNeighborhood(center=entity, nodes=sorted(nodes), edges=edges)

    async def graphe_complet(self, limite: int = 500) -> GrapheComplet:
        """Tous les faits deviennent arêtes (même logique naïve que `neighborhood`,
        sans restriction de frontière). Au-delà de `limite` nœuds, garde les plus
        connectés (degré décroissant, nom en repli pour la stabilité du tri)."""
        noms_originaux, paires = _construire_graphe_brut(self._facts)
        degre: dict[str, int] = dict.fromkeys(noms_originaux, 0)
        for source, target, _fait in paires:
            if source != target:
                degre[source] = degre.get(source, 0) + 1
                degre[target] = degre.get(target, 0) + 1
        ordonnes = sorted(noms_originaux, key=lambda n: (-degre.get(n, 0), n))
        tronque = len(ordonnes) > limite
        gardes = set(ordonnes[:limite])
        aretes_gardees = [
            self._arete_graphe(fait, source, target)
            for source, target, fait in paires
            if source in gardes and target in gardes
        ]
        noeuds = [self._noeud_graphe(n) for n in ordonnes[:limite]]
        return GrapheComplet(noeuds=noeuds, aretes=aretes_gardees, tronque=tronque)

    # --- Corrections ciblées (ticket wayfinder 0029) ---

    def _trouver_noeud_original(self, cible_uuid: str) -> str | None:
        noms_originaux, _ = _construire_graphe_brut(self._facts)
        for nom in noms_originaux:
            if _uuid_noeud(nom) == cible_uuid:
                return nom
        return None

    def _trouver_fait(self, cible_uuid: str) -> Fact | None:
        for fait in self._facts:
            if self._fact_uuids.get(id(fait)) == cible_uuid:
                return fait
        return None

    def _enregistrement_noeud(self, nom_original: str) -> dict:
        return self._corrections_noeuds.setdefault(
            nom_original.lower(),
            {
                "nom_actuel": nom_original,
                "type": None,
                "type_precedent": None,
                "nom_precedent": None,
                "corrige_le": None,
                "corrige_geste": None,
            },
        )

    def _nom_actuel(self, nom_original: str) -> str:
        enreg = self._corrections_noeuds.get(nom_original.lower())
        return enreg["nom_actuel"] if enreg else nom_original

    def _noeud_graphe(self, nom_original: str) -> NoeudGraphe:
        enreg = self._corrections_noeuds.get(nom_original.lower(), {})
        return NoeudGraphe(
            nom=enreg.get("nom_actuel", nom_original),
            uuid=_uuid_noeud(nom_original),
            type=enreg.get("type"),
            corrige_le=enreg.get("corrige_le"),
            corrige_geste=enreg.get("corrige_geste"),
            nom_precedent=enreg.get("nom_precedent"),
            type_precedent=enreg.get("type_precedent"),
        )

    def _arete_graphe(self, fait: Fact, source_original: str, target_original: str) -> GraphEdge:
        cible_uuid = self._fact_uuids.get(id(fait))
        trace = self._corrections_aretes.get(cible_uuid, {}) if cible_uuid else {}
        return GraphEdge(
            source=self._nom_actuel(source_original),
            target=self._nom_actuel(target_original),
            text=fait.text,
            provenance=fait.provenance,
            valid_at=fait.valid_at,
            invalid_at=fait.invalid_at,
            uuid=cible_uuid,
            corrige_le=trace.get("corrige_le"),
            corrige_geste=trace.get("corrige_geste"),
        )

    async def corriger_type(self, uuid: str, type_: str) -> None:
        nom_original = self._trouver_noeud_original(uuid)
        if nom_original is None:
            raise CibleIntrouvable(uuid)
        enreg = self._enregistrement_noeud(nom_original)
        enreg["type_precedent"] = enreg["type"]
        enreg["type"] = type_
        enreg["corrige_le"] = datetime.now(UTC)
        enreg["corrige_geste"] = "type"

    async def renommer_entite(self, uuid: str, nom: str) -> None:
        nom_original = self._trouver_noeud_original(uuid)
        if nom_original is None:
            raise CibleIntrouvable(uuid)
        enreg = self._enregistrement_noeud(nom_original)
        enreg["nom_precedent"] = enreg["nom_actuel"]
        enreg["nom_actuel"] = nom
        enreg["corrige_le"] = datetime.now(UTC)
        enreg["corrige_geste"] = "renommage"

    async def invalider_fait(self, uuid: str) -> None:
        fait = self._trouver_fait(uuid)
        if fait is None:
            raise CibleIntrouvable(uuid)
        fait.invalid_at = fait.valid_at or datetime.now(UTC)
        self._corrections_aretes[uuid] = {
            "corrige_le": datetime.now(UTC),
            "corrige_geste": "invalidation",
        }

    async def annuler_invalidation(self, uuid: str) -> None:
        fait = self._trouver_fait(uuid)
        if fait is None:
            raise CibleIntrouvable(uuid)
        trace = self._corrections_aretes.get(uuid)
        if not trace or trace.get("corrige_geste") != "invalidation":
            raise CorrectionRefusee(uuid)
        fait.invalid_at = None
        self._corrections_aretes.pop(uuid, None)


def _construire_graphe_brut(facts: list[Fact]) -> tuple[set[str], list[tuple[str, str, Fact]]]:
    """Toutes les entités (noms ORIGINAUX, non corrigés) et tous les faits vus
    comme paires (source, target, fait), sans restriction de frontière
    (contrairement à `neighborhood`) — utilisé par `graphe_complet`."""
    nodes: set[str] = set()
    paires: list[tuple[str, str, Fact]] = []
    for fact in facts:
        entities = _entities(fact.text)
        if not entities:
            continue
        nodes.update(entities)
        source = entities[0]
        for target in entities[1:] or [source]:
            paires.append((source, target, fact))
    return nodes, paires


def _entities(text: str) -> list[str]:
    words = re.findall(r"\b[A-ZÀ-Ý][\wà-ÿ-]*", text)
    seen: dict[str, str] = {}
    for word in words:
        if word.lower() not in _STOPWORDS:
            seen.setdefault(word.lower(), word)
    return list(seen.values())
