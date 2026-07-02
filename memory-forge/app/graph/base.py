from abc import ABC, abstractmethod

from app.schemas import EpisodeIn, Fact


class GraphMemory(ABC):
    """Port du graphe de mémoire, calqué sur les scénarios de docs/ACCEPTANCE-MEMOIRE.md
    (et non sur l'API de Graphiti) : l'implémentation est interchangeable sans toucher
    à la Filter OpenWebUI ni au serveur MCP."""

    @abstractmethod
    async def add_episode(self, episode: EpisodeIn) -> None:
        """Extrait les faits de l'épisode et les intègre au graphe (résolution d'entités,
        invalidation des faits contredits)."""

    @abstractmethod
    async def search(self, query: str) -> list[Fact]:
        """Faits pertinents pour la requête, faits actifs d'abord."""

    @abstractmethod
    async def forget(self, entity: str) -> int:
        """Oubli : suppression réelle des faits liés à l'entité. Renvoie le nombre supprimé."""
