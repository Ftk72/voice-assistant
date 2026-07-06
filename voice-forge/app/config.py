from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VOICE_FORGE_")

    voices_dir: Path = Path("voices")
    host: str = "127.0.0.1"
    port: int = 8100
    provider: Literal["fake", "chatterbox"] = "fake"
    cache_dir: Path | None = None
    chatterbox_dir: Path | None = None
