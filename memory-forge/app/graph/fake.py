import re
from datetime import UTC, datetime

from app.graph.base import GraphMemory
from app.schemas import EpisodeIn, Fact, Provenance


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
