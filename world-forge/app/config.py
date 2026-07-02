from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="WORLD_FORGE_")

    host: str = "127.0.0.1"
    port: int = 8300
    gateway: Literal["fake", "real"] = "fake"
    # Utilisés uniquement par la passerelle réelle :
    searxng_url: str = "http://searxng:8080"  # méta-moteur auto-hébergé (ADR 0007)
    geocoding_url: str = "https://geocoding-api.open-meteo.com/v1/search"
    meteo_url: str = "https://api.open-meteo.com/v1/forecast"
    # Flux RSS/Atom du briefing, séparés par des virgules.
    feeds: str = ""
    timeout_seconds: float = 15.0
    # Taille max du texte restitué d'une page (le LLM a un contexte de 8k).
    page_max_chars: int = 6000
