from datetime import date, datetime

from pydantic import BaseModel


class SearchResult(BaseModel):
    """Un résultat brut du méta-moteur — matière première de la réponse sourcée."""

    title: str
    url: str
    snippet: str


class DayForecast(BaseModel):
    day: date
    description: str  # code météo WMO traduit en français parlable
    temp_min: float
    temp_max: float
    precipitation_probability: int | None = None


class WeatherReport(BaseModel):
    place: str
    days: list[DayForecast]


class FeedItem(BaseModel):
    """Une entrée d'un flux du briefing."""

    feed: str
    title: str
    summary: str = ""
    published: datetime | None = None


class PageText(BaseModel):
    """Le texte lisible d'une page, débarrassé du balisage — pour la lecture de page."""

    url: str
    title: str
    text: str
    truncated: bool = False
