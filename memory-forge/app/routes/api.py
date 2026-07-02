from fastapi import APIRouter, Request

from app.schemas import EpisodeIn, SearchResponse

router = APIRouter()


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


@router.delete("/facts")
async def forget(entity: str, request: Request) -> dict[str, int]:
    """Oubli : suppression réelle (distincte de l'obsolescence, cf. CONTEXT.md)."""
    return {"forgotten": await request.app.state.graph.forget(entity)}
