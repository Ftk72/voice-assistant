from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TIME_FORGE_")

    host: str = "127.0.0.1"
    port: int = 8400
    store: Literal["memory", "sqlite"] = "memory"
    sqlite_path: Path = Path("agenda.db")
    announcer: Literal["log", "hostbridge"] = "log"
    # Fréquence de la vérification des annonces d'agenda (les minuteurs, eux,
    # sont précis à la seconde : tâches asyncio dédiées, pas de polling).
    agenda_poll_seconds: float = 10.0
    # Utilisés uniquement par l'annonceur hostbridge :
    voice_forge_url: str = "http://voice-forge:8100"
    # Le Pont hôte tourne sur la machine hôte, hors Docker (ADR 0008).
    host_bridge_url: str = "http://host.docker.internal:8500"
    # Jeton partagé attendu par le Pont (vide = Pont sans auth, dev local).
    host_bridge_token: str = ""
    announce_voice: str = "default"
