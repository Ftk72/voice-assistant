import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings
from app.dialogue.base import ClientDialogue
from app.dialogue.fake import ClientDialogueFactice
from app.routes.api import router
from app.stt.base import MoteurSTT
from app.stt.fake import STTFactice
from app.transport.base import Transport
from app.transport.fake import TransportFactice
from app.tts.base import MoteurTTS
from app.tts.fake import TTSFactice

logger = logging.getLogger(__name__)


def build_stt(settings: Settings) -> MoteurSTT:
    if settings.stt_backend == "whispercpp":
        from app.stt.whispercpp import STTWhisperCpp

        return STTWhisperCpp(settings.stt_base_url)
    return STTFactice()


def build_tts(settings: Settings) -> MoteurTTS:
    if settings.tts_backend == "voiceforge":
        from app.tts.voiceforge import TTSVoiceForge

        return TTSVoiceForge(settings.tts_base_url)
    return TTSFactice()


def build_dialogue(settings: Settings) -> ClientDialogue:
    if settings.dialogue_backend == "rest":
        from app.dialogue.rest import ClientDialogueREST

        return ClientDialogueREST(settings.dialogue_base_url)
    return ClientDialogueFactice()


def build_transport(settings: Settings) -> Transport:
    if settings.transport_backend == "pipecat":
        from app.transport.pipecat import TransportPipecat

        return TransportPipecat(settings)
    return TransportFactice()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    stt = build_stt(settings)
    tts = build_tts(settings)
    dialogue = build_dialogue(settings)
    transport = build_transport(settings)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        for composant in (app.state.stt, app.state.tts, app.state.dialogue):
            aclose = getattr(composant, "aclose", None)
            if aclose is not None:
                await aclose()

    app = FastAPI(title="Transport Voix", lifespan=lifespan)
    # La coquille (WebView2, origine tauri.localhost) appelle /offer en
    # cross-origin : sans CORS, son préflight OPTIONS est refusé (405).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origines,
        allow_origin_regex=settings.cors_origine_regex,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Journalise l'Origin de chaque requête /offer (via le logger uvicorn,
    # seul configuré sous `python -m app`) : c'est LA donnée qu'il faut quand
    # un client local est refusé par le CORS — ajouté après un 400 inexpliqué
    # de la coquille au premier run réel (2026-07-10). Déclaré APRÈS le
    # middleware CORS pour être plus externe que lui (Starlette empile en
    # ordre inverse) et voir aussi les préflights rejetés.
    @app.middleware("http")
    async def journaliser_origine_offer(request, call_next):
        if request.url.path == "/offer":
            logging.getLogger("uvicorn.error").info(
                "%s /offer — Origin: %r, méthode demandée: %r, en-têtes demandés: %r",
                request.method,
                request.headers.get("origin"),
                request.headers.get("access-control-request-method"),
                request.headers.get("access-control-request-headers"),
            )
        return await call_next(request)
    app.state.settings = settings
    app.state.stt = stt
    app.state.tts = tts
    app.state.dialogue = dialogue
    app.state.transport = transport
    # Connexions WebRTC vivantes, indexées par pc_id (signaling SmallWebRTC).
    app.state.webrtc_connexions = {}
    app.include_router(router)
    return app
