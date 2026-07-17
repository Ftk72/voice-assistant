"""Route du module d'interface du dialogue (A4).

Le Dialogue Forge sert sa propre UI (ADR 0009 — la coquille ne fait qu'assembler,
aucune logique métier côté coquille), sur le modèle voice-forge `/admin` et
memory-forge `/viz`. La page se charge en **iframe** dans l'onglet console de la
coquille ; elle lit le REST du DF pour le contenu (personas, historique,
dérogation de voix) et reçoit le **fil de conversation** (transcriptions et
phrases assistant, au timing de lecture) par `postMessage` depuis la console,
qui seule tient le canal RTVI (résolution du ticket 0007).
"""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).resolve().parent.parent / "module_dialogue"

router = APIRouter(prefix="/dialogue")


@router.get("", include_in_schema=False)
def page() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@router.get("/dialogue.js", include_in_schema=False)
def script() -> FileResponse:
    return FileResponse(STATIC_DIR / "dialogue.js", media_type="text/javascript")


@router.get("/dialogue.css", include_in_schema=False)
def style() -> FileResponse:
    return FileResponse(STATIC_DIR / "dialogue.css", media_type="text/css")
