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

    # --- Réglages du pipeline Pipecat réel (chemin transport_backend=pipecat) ---
    # Persona d'ouverture des conversations (None → défaut du Dialogue Forge).
    persona_defaut: str | None = None
    # STT whisper.cpp (OpenAI-compat, batch). Clé factice : service local.
    stt_model: str = "whisper"
    stt_api_key: str = "sk-local"
    # TTS voice-forge (OpenAI-compat). Persona figé ⇒ voix constante par
    # conversation (ADR 0012 décision 4) ; la VoixDeTest est le défaut du dépôt.
    tts_model: str = "voiceforge"
    tts_api_key: str = "sk-local"
    tts_voix_defaut: str = "VoixDeTest"
    # Serveurs STUN pour la négociation WebRTC. **Vide par défaut = souverain**.
    stun_urls: list[str] = []
    # TURN local (coturn, service compose). Relaie la media WebRTC : forcé des
    # deux côtés (navigateur + Pipecat), il route tout le flux par coturn et
    # contourne les blocages NAT/pare-feu du pont WSL2↔Windows sans que rien ne
    # quitte la machine (cf. docs/impasses.md). Vide = pas de TURN.
    turn_url: str = "turn:127.0.0.1:3478"
    turn_user: str = "voix"
    turn_password: str = "voixsecret"
