"""Route du réglage grand public (ticket wayfinder 0014) : persona + voix par
défaut, préférence **permanente** persistée (modèle A) — toute nouvelle
conversation créée sans persona explicite l'adopte. Page servie par le Dialogue
Forge (ADR 0009 — chaque forge sert sa propre UI), sur le modèle du module
dialogue (A4) : formulaire (variante B figée), même origine, aucune logique
métier côté coquille.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from app.preferences import Preferences, enregistrer_preferences
from app.schemas import PreferenceIn

STATIC_DIR = Path(__file__).resolve().parent.parent / "reglage"

router = APIRouter(prefix="/reglage")


@router.get("", include_in_schema=False)
def page() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/reglage.js", include_in_schema=False)
def script() -> FileResponse:
    return FileResponse(STATIC_DIR / "reglage.js", media_type="text/javascript")


@router.get("/reglage.css", include_in_schema=False)
def style() -> FileResponse:
    return FileResponse(STATIC_DIR / "reglage.css", media_type="text/css")


@router.get("/preference")
def lire_preference(request: Request) -> dict[str, str | None]:
    prefs = request.app.state.preferences
    return {"persona": prefs.persona, "voix": prefs.voix}


@router.put("/preference")
def ecrire_preference(corps: PreferenceIn, request: Request) -> dict[str, str | None]:
    personas = request.app.state.personas
    cle = corps.persona.lower()
    if cle not in personas:
        raise HTTPException(status_code=404, detail=f"Persona inconnu : {corps.persona}")
    prefs = Preferences(persona=cle, voix=corps.voix)
    request.app.state.preferences = prefs
    enregistrer_preferences(request.app.state.settings.reglage_path, prefs)
    return {"persona": prefs.persona, "voix": prefs.voix}
