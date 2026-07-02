"""Passerelle réelle — jamais exécutée à ce jour (pattern GraphitiMemory) :
à valider au premier lancement réel, avec SearXNG démarré et une connexion."""

import asyncio
from urllib.parse import urlparse

import httpx

from app.config import Settings
from app.schemas import FeedItem, PageText, SearchResult, WeatherReport
from app.world.base import WorldGateway
from app.world.htmltext import extract_text
from app.world.meteo import parse_forecast
from app.world.rss import parse_feed


class RealWorld(WorldGateway):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            timeout=settings.timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": "world-forge/0.1 (assistant vocal local)"},
        )

    async def search(self, query: str, max_results: int = 5) -> list[SearchResult]:
        # Le format JSON doit être activé dans settings.yml de SearXNG (voir searxng/).
        response = await self._client.get(
            f"{self._settings.searxng_url}/search",
            params={"q": query, "format": "json", "language": "fr"},
        )
        response.raise_for_status()
        return [
            SearchResult(
                title=result.get("title", ""),
                url=result.get("url", ""),
                snippet=result.get("content", ""),
            )
            for result in response.json().get("results", [])[:max_results]
        ]

    async def weather(self, place: str, days: int = 1) -> WeatherReport:
        geo = await self._client.get(
            self._settings.geocoding_url,
            params={"name": place, "count": 1, "language": "fr", "format": "json"},
        )
        geo.raise_for_status()
        matches = geo.json().get("results") or []
        if not matches:
            raise LookupError(f"Lieu introuvable : {place}")
        found = matches[0]
        forecast = await self._client.get(
            self._settings.meteo_url,
            params={
                "latitude": found["latitude"],
                "longitude": found["longitude"],
                "daily": "weather_code,temperature_2m_min,temperature_2m_max,"
                "precipitation_probability_max",
                "timezone": "auto",
                "forecast_days": days,
            },
        )
        forecast.raise_for_status()
        return parse_forecast(forecast.json(), place=found.get("name", place))

    async def headlines(self, max_per_feed: int = 5) -> list[FeedItem]:
        urls = [url.strip() for url in self._settings.feeds.split(",") if url.strip()]
        feeds = await asyncio.gather(
            *(self._fetch_feed(url, max_per_feed) for url in urls), return_exceptions=True
        )
        items: list[FeedItem] = []
        for feed in feeds:
            if not isinstance(feed, BaseException):  # un flux en panne ne tue pas le briefing
                items.extend(feed)
        return items

    async def _fetch_feed(self, url: str, max_items: int) -> list[FeedItem]:
        response = await self._client.get(url)
        response.raise_for_status()
        name = urlparse(url).hostname or url
        return parse_feed(response.text, feed_name=name, max_items=max_items)

    async def read_page(self, url: str) -> PageText:
        response = await self._client.get(url)
        response.raise_for_status()
        title, text = extract_text(response.text)
        limit = self._settings.page_max_chars
        return PageText(url=url, title=title, text=text[:limit], truncated=len(text) > limit)
