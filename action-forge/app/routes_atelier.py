from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).resolve().parent / "atelier_ui"

router = APIRouter()


@router.get("/atelier", include_in_schema=False)
def atelier_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
