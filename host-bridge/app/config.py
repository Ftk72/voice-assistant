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
