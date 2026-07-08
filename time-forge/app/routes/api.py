from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.schemas import Event, Timer

VIZ_PAGE = Path(__file__).resolve().parent.parent / "viz" / "index.html"

router = APIRouter()


@router.get("/agenda", include_in_schema=False)
def agenda_page() -> FileResponse:
    """Page de visualisation agenda + minuteurs (roadmap B3)."""
    return FileResponse(VIZ_PAGE)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/events", response_model=list[Event])
async def events(request: Request) -> list[Event]:
    """Accès direct pour smoke-test (7 prochains jours) ; l'assistant passe par MCP."""
    now = datetime.now()
    return await request.app.state.store.list_between(now, now + timedelta(days=7))


@router.get("/timers", response_model=list[Timer])
def timers(request: Request) -> list[Timer]:
    return request.app.state.timers.active()


class AnnouncementIn(BaseModel):
    text: str


@router.post("/announce", status_code=202)
async def announce(body: AnnouncementIn, request: Request) -> dict[str, str]:
    """Déclenche une annonce immédiate — smoke-test de la chaîne annonceur
    (Voice Forge → Pont hôte) sans attendre une échéance."""
    await request.app.state.announcer.announce(body.text)
    return {"status": "announced"}
