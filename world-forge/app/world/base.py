from abc import ABC, abstractmethod

from app.schemas import FeedItem, PageText, SearchResult, WeatherReport


class WorldGateway(ABC):
    """Port de l'accès au monde extérieur (ADR 0007 : souveraineté, pas isolement).
    L'implémentation est interchangeable sans toucher au serveur MCP : la passerelle
    factice sert aux tests et au développement hors connexion."""

    @abstractmethod
    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        """Résultats du méta-moteur pour la requête — jamais restitués tels quels :
        le LLM en fait une réponse sourcée (CONTEXT.md)."""

    @abstractmethod
    async def weather(self, place: str, days: int = 1) -> WeatherReport:
        """Prévisions pour un lieu nommé, du jour courant à J+days-1."""

    @abstractmethod
    async def headlines(self, max_per_feed: int = 5) -> list[FeedItem]:
        """Dernières entrées des flux configurés — matière première du briefing."""

    @abstractmethod
    async def read_page(self, url: str) -> PageText:
        """Texte lisible d'une page désignée par l'utilisateur (lecture de page)."""
