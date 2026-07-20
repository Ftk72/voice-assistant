"""Annonceur réel — validé au réel le 2026-07-20 (ticket 0035, annonce de fin
de Tâche entendue sur les enceintes).

Chaîne de l'annonce (ADR 0008) : l'Action Forge synthétise la parole via le
Voice Forge (même voix que l'assistant), puis envoie l'audio au Pont hôte qui
le joue sur les enceintes. Le Pont reste sans intelligence : il reçoit du wav.
"""

import logging

import httpx

from app.annonce.base import Annonceur
from app.config import Settings

logger = logging.getLogger(__name__)


class AnnonceurPontHote(Annonceur):
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client or httpx.AsyncClient(timeout=30.0)

    async def annoncer(self, texte: str) -> None:
        try:
            synthese = await self._client.post(
                f"{self._settings.voice_forge_url}/v1/audio/speech",
                json={
                    "model": "tts-1",
                    "input": texte,
                    "voice": self._settings.annonce_voix,
                    "response_format": "wav",
                },
            )
            synthese.raise_for_status()
            entetes = {"Content-Type": "audio/wav"}
            if self._settings.host_bridge_token:
                entetes["X-Bridge-Token"] = self._settings.host_bridge_token
            jouee = await self._client.post(
                f"{self._settings.host_bridge_url}/play",
                content=synthese.content,
                headers=entetes,
            )
            jouee.raise_for_status()
        except httpx.HTTPError:
            # Une annonce ratée ne doit jamais tuer une Tâche.
            logger.exception("Échec de l'annonce : %s", texte)
