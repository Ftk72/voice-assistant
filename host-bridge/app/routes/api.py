from fastapi import APIRouter, HTTPException, Request, Response

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/actions")
def actions(request: Request) -> list[dict[str, str]]:
    """Le catalogue exposé (nom + description, sans les argv) — smoke-test et
    inspection ; l'assistant passe par MCP."""
    catalog = request.app.state.catalog
    return [{"name": a.name, "description": a.description} for a in catalog.values()]


@router.post("/actions/{name}", status_code=200)
def run_action(name: str, request: Request) -> dict[str, str]:
    """Exécute une action du catalogue (404 si hors liste blanche)."""
    catalog = request.app.state.catalog
    action = catalog.get(name)
    if action is None:
        raise HTTPException(status_code=404, detail="Action hors liste blanche.")
    result = request.app.state.runner.run(action)
    return {"result": result}


@router.post("/play", status_code=202)
async def play(request: Request) -> Response:
    """Reçoit un wav prêt à jouer (corps brut) et le confie au lecteur — c'est le
    canal de l'annonceur du Time Forge vers les enceintes (ADR 0008)."""
    data = await request.body()
    request.app.state.player.play_wav(data)
    return Response(status_code=202)
