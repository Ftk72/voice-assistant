import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI

from app.announce.base import Announcer
from app.announce.log import LogAnnouncer
from app.config import Settings
from app.mcp_server import build_mcp
from app.routes.api import router
from app.store.base import AgendaStore
from app.store.memory import InMemoryAgenda
from app.timers import TimerBoard

logger = logging.getLogger(__name__)


def build_store(settings: Settings) -> AgendaStore:
    if settings.store == "sqlite":
        from app.store.sqlite import SqliteAgenda

        return SqliteAgenda(settings.sqlite_path)
    return InMemoryAgenda()


def build_announcer(settings: Settings) -> Announcer:
    if settings.announcer == "hostbridge":
        from app.announce.hostbridge import HostBridgeAnnouncer

        return HostBridgeAnnouncer(settings)
    return LogAnnouncer()


def announcement_text(title: str, lead_minutes: int | None) -> str:
    if not lead_minutes:
        return f"Rappel : {title}."
    return f"Dans {lead_minutes} minutes : {title}."


async def agenda_loop(store: AgendaStore, announcer: Announcer, poll_seconds: float) -> None:
    """Vérifie périodiquement les annonces dues — la parole spontanée passe
    uniquement par l'annonceur (CONTEXT.md)."""
    while True:
        try:
            for event in await store.claim_due(datetime.now()):
                await announcer.announce(
                    announcement_text(event.title, event.announce_lead_minutes)
                )
        except Exception:
            logger.exception("Échec de la boucle d'agenda")
        await asyncio.sleep(poll_seconds)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    store = build_store(settings)
    announcer = build_announcer(settings)
    timers = TimerBoard(announcer)
    mcp = build_mcp(store, timers)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        task = asyncio.create_task(agenda_loop(store, announcer, settings.agenda_poll_seconds))
        async with mcp.session_manager.run():
            yield
        task.cancel()
        timers.shutdown()

    app = FastAPI(title="Time Forge", lifespan=lifespan)
    app.state.settings = settings
    app.state.store = store
    app.state.announcer = announcer
    app.state.timers = timers
    app.include_router(router)
    app.mount("/mcp", mcp.streamable_http_app())
    return app
