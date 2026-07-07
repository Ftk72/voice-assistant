import re
from datetime import UTC, datetime

from app.graph.base import GraphMemory
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


class InMemoryGraph(GraphMemory):
    """Graphe factice pour les tests et le développement sans Neo4j/LLM :
    une phrase = un fait, recherche par simple inclusion de mots."""

    def __init__(self) -> None:
        self._facts: list[Fact] = []

    async def add_episode(self, episode: EpisodeIn) -> None:
        provenance = Provenance(source=episode.source, name=episode.name)
        for sentence in re.split(r"(?<=[.!?])\s+", episode.content):
            if sentence.strip():
                self._facts.append(
                    Fact(
                        text=sentence.strip(),
                        provenance=provenance,
                        valid_at=datetime.now(UTC),
                    )
                )

    async def search(self, query: str) -> list[Fact]:
        words = query.lower().split()
        return [
            fact for fact in self._facts if any(word in fact.text.lower() for word in words)
        ]

    async def forget(self, entity: str) -> int:
        before = len(self._facts)
        self._facts = [f for f in self._facts if entity.lower() not in f.text.lower()]
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
                nodes.update(entities)
                reached.update(e.lower() for e in entities)
                source = entities[0]
                for target in entities[1:] or [source]:
                    edges.append(
                        GraphEdge(
                            source=source,
                            target=target,
                            text=fact.text,
                            provenance=fact.provenance,
                            valid_at=fact.valid_at,
                            invalid_at=fact.invalid_at,
                        )
                    )
            frontier = reached - visited
            if not frontier:
                break
        return GraphNeighborhood(center=entity, nodes=sorted(nodes), edges=edges)

    async def graphe_complet(self, limite: int = 500) -> GrapheComplet:
        """Tous les faits deviennent arêtes (même logique naïve que `neighborhood`,
        sans restriction de frontière). Au-delà de `limite` nœuds, garde les plus
        connectés (degré décroissant, nom en repli pour la stabilité du tri)."""
        nodes, edges = _construire_graphe(self._facts)
        degre: dict[str, int] = dict.fromkeys(nodes, 0)
        for edge in edges:
            if edge.source != edge.target:
                degre[edge.source] = degre.get(edge.source, 0) + 1
                degre[edge.target] = degre.get(edge.target, 0) + 1
        ordonnes = sorted(nodes, key=lambda n: (-degre.get(n, 0), n))
        tronque = len(ordonnes) > limite
        gardes = set(ordonnes[:limite])
        aretes_gardees = [e for e in edges if e.source in gardes and e.target in gardes]
        noeuds = [NoeudGraphe(nom=n) for n in ordonnes[:limite]]
        return GrapheComplet(noeuds=noeuds, aretes=aretes_gardees, tronque=tronque)


def _construire_graphe(facts: list[Fact]) -> tuple[set[str], list[GraphEdge]]:
    """Toutes les entités et tous les faits vus comme arêtes, sans restriction de
    frontière (contrairement à `neighborhood`) — utilisé par `graphe_complet`."""
    nodes: set[str] = set()
    edges: list[GraphEdge] = []
    for fact in facts:
        entities = _entities(fact.text)
        if not entities:
            continue
        nodes.update(entities)
        source = entities[0]
        for target in entities[1:] or [source]:
            edges.append(
                GraphEdge(
                    source=source,
                    target=target,
                    text=fact.text,
                    provenance=fact.provenance,
                    valid_at=fact.valid_at,
                    invalid_at=fact.invalid_at,
                )
            )
    return nodes, edges


def _entities(text: str) -> list[str]:
    words = re.findall(r"\b[A-ZÀ-Ý][\wà-ÿ-]*", text)
    seen: dict[str, str] = {}
    for word in words:
        if word.lower() not in _STOPWORDS:
            seen.setdefault(word.lower(), word)
    return list(seen.values())
