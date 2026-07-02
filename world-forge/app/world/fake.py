from datetime import UTC, date, datetime, timedelta

from app.schemas import DayForecast, FeedItem, PageText, SearchResult, WeatherReport
from app.world.base import WorldGateway


class FakeWorld(WorldGateway):
    """Passerelle factice pour les tests et le développement hors connexion :
    données en dur, aucune requête réseau."""

    def __init__(self) -> None:
        self.results: list[SearchResult] = [
            SearchResult(
                title="Python 3.13 — notes de version",
                url="https://docs.python.org/3.13/whatsnew/",
                snippet="Python 3.13 apporte un REPL amélioré et un mode sans GIL expérimental.",
            )
        ]
        self.items: list[FeedItem] = [
            FeedItem(
                feed="Le Monde",
                title="Titre factice du jour",
                summary="Résumé factice.",
                published=datetime.now(UTC),
            )
        ]
        self.pages: dict[str, PageText] = {}

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        return self.results[:max_results]

    async def weather(self, place: str, days: int = 1) -> WeatherReport:
        return WeatherReport(
            place=place,
            days=[
                DayForecast(
                    day=date.today() + timedelta(days=offset),
                    description="ciel dégagé",
                    temp_min=12.0,
                    temp_max=24.0,
                    precipitation_probability=5,
                )
                for offset in range(days)
            ],
        )

    async def headlines(self, max_per_feed: int = 5) -> list[FeedItem]:
        return self.items[:max_per_feed]

    async def read_page(self, url: str) -> PageText:
        return self.pages.get(
            url, PageText(url=url, title="Page factice", text="Contenu factice de la page.")
        )
