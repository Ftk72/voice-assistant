from fastapi import FastAPI

from app.config import Settings
from app.providers.factory import build_provider
from app.routes.admin import router as admin_router
from app.routes.openai_audio import router
from app.voices.manager import VoiceManager


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    app = FastAPI(title="Voice Forge")
    app.state.settings = settings
    app.state.voice_manager = VoiceManager(settings.voices_dir)
    app.state.provider = build_provider(settings)
    app.include_router(router)
    app.include_router(router, prefix="/v1", include_in_schema=False)
    app.include_router(admin_router)
    return app
