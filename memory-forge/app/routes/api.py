from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse

from app.schemas import EpisodeIn, GraphNeighborhood, SearchResponse

VIZ_PAGE = Path(__file__).resolve().parent.parent / "viz" / "index.html"

router = APIRouter()


@router.get("/viz", include_in_schema=False)
def viz_page() -> FileResponse:
    """Mini-page de visualisation navigable du graphe (phase 5, pattern admin voice-forge)."""
    return FileResponse(VIZ_PAGE)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/episodes", status_code=202)
def enqueue_episode(episode: EpisodeIn, request: Request) -> dict[str, str]:
    """202 immédiat : la capture ne doit jamais bloquer OpenWebUI.
    L'extraction se fait dans la file, en différé."""
    request.app.state.queue.put_nowait(episode)
    return {"status": "queued"}


@router.get("/search", response_model=SearchResponse)
async def search(q: str, request: Request) -> SearchResponse:
    return SearchResponse(facts=await request.app.state.graph.search(q))


@router.get("/graph", response_model=GraphNeighborhood)
async def graph(
    entity: str, request: Request, depth: int = Query(default=1, ge=1, le=3)
) -> GraphNeighborhood:
    """Voisinage navigable d'une entité — consommé par la page /viz (phase 5)."""
    return await request.app.state.graph.neighborhood(entity, depth=depth)


@router.delete("/facts")
async def forget(entity: str, request: Request) -> dict[str, int]:
    """Oubli : suppression réelle (distincte de l'obsolescence, cf. CONTEXT.md)."""
    return {"forgotten": await request.app.state.graph.forget(entity)}
