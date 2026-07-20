import logging

from fastapi import APIRouter, HTTPException, Request, Response

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    """Santé, plus le **canal d'annonce retenu** (ticket 0044). Sans cette
    exposition, un Pont lancé sans `HOST_BRIDGE_CANAL_CONVERSATION=transport`
    dégrade en `fake` — il joue tout sur les enceintes — avec des logs et une
    santé rigoureusement identiques à un lancement correct. C'est le mode
    d'échec silencieux consigné dans `docs/impasses.md` le 2026-07-20 : on le
    rend constatable au `curl`."""
    return {"status": "ok", "canal_conversation": request.app.state.settings.canal_conversation}


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
    """Reçoit un wav prêt à jouer (corps brut) et **arbitre sa sortie** (ADR 0008,
    ticket wayfinder 0044).

    Les annonceurs (minuteur du Time Forge, fin de Tâche de l'Action Forge)
    postent ici sans rien savoir de l'état d'une conversation. C'est le Pont qui
    demande au transport : conversation ouverte (micro vif) → l'annonce part
    dans le flux WebRTC sortant, où l'annulation d'écho de la coquille la voit
    et la soustrait du micro ; sinon → les enceintes, comme avant. Sans cet
    arbitrage, l'annonce rentre par le micro, le STT la transcrit, et
    l'assistant répond à sa propre voix (constaté au réel le 2026-07-20)."""
    data = await request.body()
    canal = request.app.state.canal_conversation
    try:
        if await canal.conversation_ouverte() and await canal.jouer_annonce(data):
            return Response(status_code=202)
    except Exception:
        # Repli délibéré et sans condition : transport injoignable, timeout,
        # 5xx… une annonce doit **toujours** être entendue. Mieux vaut un écho
        # qu'un silence — le défaut que corrige le ticket 0044 est bien moins
        # grave qu'un minuteur qui ne sonne pas.
        logger.warning(
            "Canal de conversation indisponible : repli de l'annonce sur les enceintes.",
            exc_info=True,
        )
    request.app.state.player.play_wav(data)
    return Response(status_code=202)
