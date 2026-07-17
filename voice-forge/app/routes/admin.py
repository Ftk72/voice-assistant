from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.decodeurs.base import FormatAudioNonSupporte
from app.schemas import Voice
from app.voices.manager import VOICE_NAME_PATTERN

STATIC_DIR = Path(__file__).resolve().parent.parent / "admin"

router = APIRouter(prefix="/admin")


@router.get("", include_in_schema=False)
def admin_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@router.post("/api/voices", status_code=201, response_model=Voice)
async def import_voice(
    request: Request,
    name: Annotated[str, Form(pattern=VOICE_NAME_PATTERN)],
    speaker: UploadFile,
) -> Voice:
    speaker_bytes = await speaker.read()
    if speaker_bytes[0:4] != b"RIFF" or speaker_bytes[8:12] != b"WAVE":
        # Non-WAV : on tente un décodage (mp3, m4a, ogg, flac…) vers WAV de référence.
        try:
            speaker_bytes = request.app.state.decodeur.en_wav(speaker_bytes)
        except FormatAudioNonSupporte as erreur:
            raise HTTPException(status_code=415, detail="Format audio non supporté.") from erreur
    try:
        return request.app.state.voice_manager.create_voice(name, speaker_bytes)
    except FileExistsError:
        raise HTTPException(status_code=409, detail=f"La voix « {name} » existe déjà") from None


@router.delete("/api/voices/{voice_id}", status_code=204)
def delete_voice(voice_id: str, request: Request) -> None:
    if not request.app.state.voice_manager.delete_voice(voice_id):
        raise HTTPException(status_code=404, detail=f"Voix inconnue : {voice_id}")


class PreviewRequest(BaseModel):
    text: str = "Bonjour, voici un aperçu de cette voix."


@router.post("/api/voices/{voice_id}/preview")
def preview_voice(voice_id: str, body: PreviewRequest, request: Request) -> Response:
    speaker_wav = request.app.state.voice_manager.speaker_wav(voice_id)
    if speaker_wav is None:
        raise HTTPException(status_code=404, detail=f"Voix inconnue : {voice_id}")
    provider = request.app.state.provider
    audio = provider.synthesize(body.text, speaker_wav)
    return Response(content=audio, media_type=provider.media_type)
