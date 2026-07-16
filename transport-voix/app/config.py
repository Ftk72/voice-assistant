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
    # Origines autorisées à appeler le transport en cross-origin : la coquille
    # (Tauri v2 sert son front sous http://tauri.localhost sur Windows/WebView2 ;
    # variantes selon plateforme). Sans elles, le préflight OPTIONS /offer est
    # refusé (405) et la console ne peut pas ouvrir la conversation.
    cors_origines: list[str] = [
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ]
    # Filet regex en complément de la liste : toutes les variantes locales
    # légitimes (tauri.localhost, localhost/127.0.0.1 avec port). Le service
    # n'écoute que sur 127.0.0.1 ; aucune origine distante n'est admise.
    cors_origine_regex: str = (
        r"^(https?://(tauri\.localhost|localhost|127\.0\.0\.1)(:\d+)?|tauri://localhost)$"
    )
    # Serveurs STUN pour la négociation WebRTC. **Vide par défaut = souverain**.
    stun_urls: list[str] = []
    # TURN optionnel. Vide par défaut : coquille et transport sont co-localisés
    # sur l'hôte Windows, la media passe en localhost sans relais (le détour
    # coturn de l'époque WSL2↔navigateur est une impasse résolue, cf.
    # docs/impasses.md 2026-07-08 ; un TURN mort ne ferait que ralentir l'ICE).
    turn_url: str = ""
    turn_user: str = "voix"
    turn_password: str = "voixsecret"
