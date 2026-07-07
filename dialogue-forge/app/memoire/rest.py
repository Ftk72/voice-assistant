"""Adaptateur mémoire réel : REST vers memory-forge.

**Validé en réel le 2026-07-07** contre memory-forge (`memory_forge_url`) :
recherche (`GET /search`) et capture d'épisode (`POST /episodes`, traité de
façon asynchrone côté memory-forge). Aucun test ne l'instancie ni ne le joint
(zéro réseau dans la suite automatisée).

Contrat repris tel quel de memory-forge (app/routes/api.py, app/schemas.py) :
`GET /search?q=` → `{"facts": [{"text": ...}, ...]}` ;
`POST /episodes` ← `{"content", "source", "name"}` (schéma `EpisodeIn`).
"""

import httpx

from app.config import Settings
from app.memoire.base import MoteurMemoire


class MemoireREST(MoteurMemoire):
    def __init__(self, settings: Settings) -> None:
        self._client = httpx.AsyncClient(
            base_url=settings.memory_forge_url,
            timeout=httpx.Timeout(15.0, connect=5.0),
        )

    async def rechercher(self, question: str) -> list[str]:
        reponse = await self._client.get("/search", params={"q": question})
        reponse.raise_for_status()
        return [fait["text"] for fait in reponse.json().get("facts", [])]

    async def capturer_episode(self, contenu: str, nom: str) -> None:
        reponse = await self._client.post(
            "/episodes",
            json={"content": contenu, "source": "conversation", "name": nom},
        )
        reponse.raise_for_status()

    async def aclose(self) -> None:
        await self._client.aclose()
