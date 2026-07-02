from fastapi import APIRouter, Query, Request

from app.schemas import SearchResult, WeatherReport

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/search", response_model=list[SearchResult])
async def search(q: str, request: Request) -> list[SearchResult]:
    """Accès direct pour smoke-test (pattern /search du Memory Forge) ;
    l'assistant passe par MCP."""
    return await request.app.state.world.search(q)


@router.get("/weather", response_model=WeatherReport)
async def weather(
    place: str, request: Request, days: int = Query(default=2, ge=1, le=7)
) -> WeatherReport:
    return await request.app.state.world.weather(place, days=days)
