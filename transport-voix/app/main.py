import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
    app.state.settings = settings
    app.state.stt = stt
    app.state.tts = tts
    app.state.dialogue = dialogue
    app.state.transport = transport
    # Connexions WebRTC vivantes, indexées par pc_id (signaling SmallWebRTC).
    app.state.webrtc_connexions = {}
    app.include_router(router)
    return app
