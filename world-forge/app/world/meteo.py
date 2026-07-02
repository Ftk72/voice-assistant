"""Traduction des réponses Open-Meteo (API anonyme, sans clé — ADR 0007) en
prévisions parlables."""

from datetime import date

from app.schemas import DayForecast, WeatherReport

# Codes météo WMO → description française prononçable.
WMO_CODES: dict[int, str] = {
    0: "ciel dégagé",
    1: "plutôt dégagé",
    2: "partiellement nuageux",
    3: "couvert",
    45: "brouillard",
    48: "brouillard givrant",
    51: "bruine légère",
    53: "bruine",
    55: "bruine dense",
    56: "bruine verglaçante",
    57: "bruine verglaçante dense",
    61: "pluie faible",
    63: "pluie",
    65: "pluie forte",
    66: "pluie verglaçante",
    67: "pluie verglaçante forte",
    71: "neige faible",
    73: "neige",
    75: "neige forte",
    77: "neige en grains",
    80: "averses faibles",
    81: "averses",
    82: "averses violentes",
    85: "averses de neige",
    86: "fortes averses de neige",
    95: "orage",
    96: "orage avec grêle",
    99: "orage avec forte grêle",
}


def describe_code(code: int) -> str:
    return WMO_CODES.get(code, "conditions indéterminées")


def parse_forecast(payload: dict, place: str) -> WeatherReport:
    """Construit le rapport depuis la réponse `daily` d'Open-Meteo."""
    daily = payload["daily"]
    probabilities = daily.get("precipitation_probability_max") or [None] * len(daily["time"])
    days = [
        DayForecast(
            day=date.fromisoformat(day),
            description=describe_code(code),
            temp_min=t_min,
            temp_max=t_max,
            precipitation_probability=probability,
        )
        for day, code, t_min, t_max, probability in zip(
            daily["time"],
            daily["weather_code"],
            daily["temperature_2m_min"],
            daily["temperature_2m_max"],
            probabilities,
            strict=True,
        )
    ]
    return WeatherReport(place=place, days=days)
