"""Adaptateur STT réel (whisper.cpp, API compatible OpenAI).

⚠️ Jamais exécuté à ce jour — cf. CLAUDE.md. Ne pas présenter comme
fonctionnel tant qu'il n'a pas tourné contre un vrai conteneur whisper.cpp.
"""

import httpx

from app.stt.base import MoteurSTT


class STTWhisperCpp(MoteurSTT):
    """Appelle l'API de transcription OpenAI-compatible exposée par
    whisper.cpp (`POST /audio/transcriptions`, multipart)."""

    def __init__(self, base_url: str, modele: str = "whisper") -> None:
        self._modele = modele
        self._client = httpx.AsyncClient(base_url=base_url)

    async def transcrire(self, audio: bytes, *, langue: str = "fr") -> str:
        reponse = await self._client.post(
            "/audio/transcriptions",
            files={"file": ("audio.wav", audio, "audio/wav")},
            data={"model": self._modele},
        )
        reponse.raise_for_status()
        return reponse.json()["text"]

    async def aclose(self) -> None:
        await self._client.aclose()
