import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.actions.base import ActionRunner
from app.actions.fake import FakeRunner
from app.audio.base import AudioPlayer
from app.audio.fake import FakePlayer
from app.catalog import load_catalog
from app.config import Settings
from app.conversation.base import CanalConversation
from app.conversation.fake import CanalFactice
from app.mcp_server import build_mcp
from app.routes.api import router


def build_runner(settings: Settings) -> ActionRunner:
    if settings.runner == "subprocess":
        from app.actions.subprocess_runner import SubprocessRunner

        return SubprocessRunner()
    return FakeRunner()


def build_player(settings: Settings) -> AudioPlayer:
    if settings.player == "auto":
        from app.audio.system import SystemPlayer

        return SystemPlayer()
    return FakePlayer()


def build_canal_conversation(settings: Settings) -> CanalConversation:
    if settings.canal_conversation == "transport":
        from app.conversation.transport import CanalTransportVoix

        return CanalTransportVoix(settings.transport_voix_url)
    return CanalFactice()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    catalog = load_catalog(settings.catalog_path)
    runner = build_runner(settings)
    player = build_player(settings)
    canal_conversation = build_canal_conversation(settings)
    mcp = build_mcp(catalog, runner)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with mcp.session_manager.run():
            yield

    app = FastAPI(title="Host Bridge", lifespan=lifespan)
    app.state.settings = settings
    app.state.catalog = catalog
    app.state.runner = runner
    app.state.player = player
    app.state.canal_conversation = canal_conversation
    app.include_router(router)
    app.mount("/mcp", mcp.streamable_http_app())

    if settings.token:
        # Middleware plutôt que dépendance FastAPI : il couvre aussi le
        # sous-serveur MCP monté sur /mcp.
        @app.middleware("http")
        async def verifier_le_jeton(request: Request, call_next):
            if request.url.path == "/health":
                return await call_next(request)
            fourni = request.headers.get("X-Bridge-Token", "")
            if not secrets.compare_digest(fourni, settings.token):
                return JSONResponse({"detail": "jeton invalide"}, status_code=401)
            return await call_next(request)

    return app
