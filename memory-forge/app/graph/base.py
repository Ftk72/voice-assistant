from abc import ABC, abstractmethod

from app.schemas import EpisodeIn, Fact, GrapheComplet, GraphNeighborhood


class GraphMemory(ABC):
    """Port du graphe de mémoire, calqué sur les scénarios de docs/ACCEPTANCE-MEMOIRE.md
    (et non sur l'API de Graphiti) : l'implémentation est interchangeable sans toucher
    à la Filter OpenWebUI ni au serveur MCP."""

    async def initialize(self) -> None:  # noqa: B027 — hook volontairement no-op par défaut
        """Préparation unique au démarrage (index, contraintes…) — no-op par défaut."""

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

    @abstractmethod
    async def neighborhood(self, entity: str, depth: int = 1) -> GraphNeighborhood:
        """Voisinage d'une entité, étendu de proche en proche jusqu'à `depth` sauts —
        alimente la visualisation (scénario visualisation d'ACCEPTANCE-MEMOIRE.md)."""

    @abstractmethod
    async def graphe_complet(self, limite: int = 500) -> GrapheComplet:
        """Le graphe entier (nœuds + arêtes = faits, provenance et validité comprises).
        Si le graphe dépasse `limite` nœuds, garde les plus connectés (degré décroissant)
        et les arêtes qui les relient entre eux — jamais d'omission silencieuse des faits
        obsolètes (invalid_at non nul), seulement marqués. Alimente la vue 3D (ADR 0010
        point 6, roadmap B1) ; l'enrichissement communauté/centralité vit dans
        app/viz/analyse.py, pas dans le port."""
