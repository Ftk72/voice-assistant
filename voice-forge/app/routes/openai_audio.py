from fastapi import APIRouter, HTTPException, Request, Response

from app.schemas import SpeechRequest, VoicesResponse

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/audio/voices", response_model=VoicesResponse)
def list_voices(request: Request) -> VoicesResponse:
    return VoicesResponse(voices=request.app.state.voice_manager.list_voices())


@router.get("/models")
def list_models() -> dict:
    """Format OpenAI minimal : OpenWebUI l'appelle pour lister les modèles TTS."""
    return {
        "object": "list",
        "data": [{"id": "tts-1", "object": "model", "owned_by": "voice-forge"}],
    }


@router.post("/audio/speech")
def speech(body: SpeechRequest, request: Request) -> Response:
    speaker_wav = request.app.state.voice_manager.speaker_wav(body.voice)
    if speaker_wav is None:
        raise HTTPException(status_code=400, detail=f"Voix inconnue : {body.voice}")
    provider = request.app.state.provider
    audio = provider.synthesize(body.input, speaker_wav)
    return Response(content=audio, media_type=provider.media_type)
