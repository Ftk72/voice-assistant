"""Adaptateur TTS réel (voice-forge).

⚠️ Jamais exécuté à ce jour — cf. CLAUDE.md. Ne pas présenter comme
fonctionnel tant qu'il n'a pas tourné contre une vraie instance voice-forge.
"""

import httpx

from app.tts.base import MoteurTTS


class TTSVoiceForge(MoteurTTS):
    """Appelle l'API de synthèse de voice-forge (`POST /audio/speech`)."""

    def __init__(self, base_url: str, modele: str = "voiceforge") -> None:
        self._modele = modele
        self._client = httpx.AsyncClient(base_url=base_url)

    async def synthetiser(self, texte: str, *, voix: str) -> bytes:
        reponse = await self._client.post(
            "/audio/speech",
            json={"input": texte, "voice": voix, "model": self._modele},
        )
        reponse.raise_for_status()
        return reponse.content

    async def aclose(self) -> None:
        await self._client.aclose()
