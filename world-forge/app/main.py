from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.mcp_server import build_mcp
from app.routes.api import router
from app.world.base import WorldGateway
from app.world.fake import FakeWorld


def build_world(settings: Settings) -> WorldGateway:
    if settings.gateway == "real":
        from app.world.real import RealWorld

        return RealWorld(settings)
    return FakeWorld()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    world = build_world(settings)
    mcp = build_mcp(world)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with mcp.session_manager.run():
            yield

    app = FastAPI(title="World Forge", lifespan=lifespan)
    app.state.settings = settings
    app.state.world = world
    app.include_router(router)
    app.mount("/mcp", mcp.streamable_http_app())
    return app
