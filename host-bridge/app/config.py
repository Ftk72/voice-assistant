from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HOST_BRIDGE_")

    # Le Pont doit être joignable depuis les conteneurs (host.docker.internal) :
    # en usage réel, écouter sur 0.0.0.0 et laisser le pare-feu limiter au réseau
    # Docker (voir README — le Pont n'expose que la liste blanche, jamais un shell).
    host: str = "127.0.0.1"
    port: int = 8500
    catalog_path: Path = Path("catalog.toml")
    runner: Literal["fake", "subprocess"] = "fake"
    player: Literal["fake", "auto"] = "fake"
    # Canal de conversation : à qui demander si une conversation est ouverte,
    # pour y router les annonces au lieu des enceintes (ticket wayfinder 0044).
    canal_conversation: Literal["fake", "transport"] = "fake"
    # Le transport-voix tourne en **natif Windows**, hors docker compose (seule
    # la coquille peut lui donner la media WebRTC) : c'est donc une URL d'hôte,
    # jamais un nom de service Docker.
    transport_voix_url: str = "http://127.0.0.1:8700"
    # Jeton partagé exigé sur toutes les routes sauf /health quand il est défini
    # (le Pont écoute sur 0.0.0.0 en usage réel : seule la stack doit pouvoir
    # déclencher les actions). Vide = auth désactivée (dev local).
    token: str = ""
