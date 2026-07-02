from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.actions.base import ActionRunner
from app.actions.fake import FakeRunner
from app.audio.base import AudioPlayer
from app.audio.fake import FakePlayer
from app.catalog import load_catalog
from app.config import Settings
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


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    catalog = load_catalog(settings.catalog_path)
    runner = build_runner(settings)
    player = build_player(settings)
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
    app.include_router(router)
    app.mount("/mcp", mcp.streamable_http_app())
    return app
