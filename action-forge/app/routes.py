import json

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.gestionnaire import GestionnaireTaches
from app.schemas import Tache, TacheIn

router = APIRouter()


def _gestionnaire(request: Request) -> GestionnaireTaches:
    return request.app.state.gestionnaire


def _tache_ou_404(gestionnaire: GestionnaireTaches, tache_id: str) -> Tache:
    tache = gestionnaire.obtenir(tache_id)
    if tache is None:
        raise HTTPException(status_code=404, detail="Tâche inconnue")
    return tache


@router.post("/taches", status_code=202)
async def confier_tache(corps: TacheIn, request: Request) -> Tache:
    return _gestionnaire(request).confier(corps.enonce)


@router.get("/taches")
async def lister_taches(request: Request) -> list[Tache]:
    return _gestionnaire(request).lister()


@router.get("/taches/{tache_id}")
async def obtenir_tache(tache_id: str, request: Request) -> Tache:
    return _tache_ou_404(_gestionnaire(request), tache_id)


@router.post("/taches/{tache_id}/annulation")
async def annuler_tache(tache_id: str, request: Request) -> Tache:
    gestionnaire = _gestionnaire(request)
    _tache_ou_404(gestionnaire, tache_id)
    await gestionnaire.annuler(tache_id)
    return gestionnaire.obtenir(tache_id)


@router.get("/taches/{tache_id}/flux")
async def flux_tache(tache_id: str, request: Request) -> StreamingResponse:
    gestionnaire = _gestionnaire(request)
    _tache_ou_404(gestionnaire, tache_id)

    async def evenements():
        async for evenement in gestionnaire.flux(tache_id):
            donnees = {
                cle: (valeur.model_dump() if hasattr(valeur, "model_dump") else valeur)
                for cle, valeur in evenement.items()
            }
            yield f"data: {json.dumps(donnees, ensure_ascii=False)}\n\n"

    return StreamingResponse(evenements(), media_type="text/event-stream")
