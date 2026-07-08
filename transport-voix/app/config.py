from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TRANSPORT_VOIX_")

    host: str = "127.0.0.1"
    port: int = 8700
    langue: str = "fr"

    stt_backend: Literal["fake", "whispercpp"] = "fake"
    # whisper.cpp, port debug direct du conteneur stt
    stt_base_url: str = "http://127.0.0.1:8002/v1"

    tts_backend: Literal["fake", "voiceforge"] = "fake"
    tts_base_url: str = "http://127.0.0.1:8100"  # voice-forge

    dialogue_backend: Literal["fake", "rest"] = "fake"
    dialogue_base_url: str = "http://127.0.0.1:8600"  # Dialogue Forge

    transport_backend: Literal["fake", "pipecat"] = "fake"
