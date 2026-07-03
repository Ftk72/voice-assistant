"""Annonceur réel — jamais exécuté à ce jour (pattern GraphitiMemory).

Chaîne de l'annonce (ADR 0008) : le Time Forge synthétise la parole via le
Voice Forge (même voix que l'assistant), puis envoie l'audio au Pont hôte qui
le joue sur les enceintes. Le Pont reste sans intelligence : il reçoit du wav.
"""

import logging

import httpx

from app.announce.base import Announcer
from app.config import Settings

logger = logging.getLogger(__name__)


class HostBridgeAnnouncer(Announcer):
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._client = client or httpx.AsyncClient(timeout=30.0)

    async def announce(self, text: str) -> None:
        try:
            speech = await self._client.post(
                f"{self._settings.voice_forge_url}/v1/audio/speech",
                json={
                    "model": "tts-1",
                    "input": text,
                    "voice": self._settings.announce_voice,
                    "response_format": "wav",
                },
            )
            speech.raise_for_status()
            headers = {"Content-Type": "audio/wav"}
            if self._settings.host_bridge_token:
                headers["X-Bridge-Token"] = self._settings.host_bridge_token
            played = await self._client.post(
                f"{self._settings.host_bridge_url}/play",
                content=speech.content,
                headers=headers,
            )
            played.raise_for_status()
        except httpx.HTTPError:
            # Une annonce ratée ne doit jamais tuer la boucle d'agenda.
            logger.exception("Échec de l'annonce : %s", text)
