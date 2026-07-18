"""Adaptateur réel, contrat repris de voice-forge.

`GET /audio/voices` → `{"voices": [{"id": ..., "name": ...}, ...]}` (mappe
`name` → `nom`) ; `POST /admin/api/voices/{voix_id}/preview` (corps `{}`) →
audio/wav en réponse. Aucun test ne l'instancie ni ne le joint (zéro réseau
dans la suite automatisée).

Validé en réel le 2026-07-17 (ticket wayfinder 0014) : liste complète des voix
enrôlées servie à la page de réglage via `GET /voix` du DF, aperçu audible.
"""

import httpx

from app.config import Settings
from app.voix.base import CatalogueVoix


class CatalogueVoixREST(CatalogueVoix):
    def __init__(self, settings: Settings) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.voice_forge_url,
            timeout=httpx.Timeout(15.0, connect=5.0),
        )

    async def lister(self) -> list[dict]:
        reponse = await self._client.get("/audio/voices")
        reponse.raise_for_status()
        return [
            {"id": voix["id"], "nom": voix["name"]}
            for voix in reponse.json().get("voices", [])
        ]

    async def apercu(self, voix_id: str) -> bytes:
        reponse = await self._client.post(f"/admin/api/voices/{voix_id}/preview", json={})
        reponse.raise_for_status()
        return reponse.content

    async def aclose(self) -> None:
        await self._client.aclose()
