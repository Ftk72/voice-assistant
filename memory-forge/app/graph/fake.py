import re
from datetime import UTC, datetime

from app.graph.base import GraphMemory
from app.schemas import EpisodeIn, Fact, GraphEdge, GraphNeighborhood, Provenance

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


def _entities(text: str) -> list[str]:
    words = re.findall(r"\b[A-ZÀ-Ý][\wà-ÿ-]*", text)
    seen: dict[str, str] = {}
    for word in words:
        if word.lower() not in _STOPWORDS:
            seen.setdefault(word.lower(), word)
    return list(seen.values())
