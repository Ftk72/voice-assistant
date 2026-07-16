"""Adaptateur de dialogue réel (client REST du Dialogue Forge).

⚠️ Jamais exécuté à ce jour — cf. CLAUDE.md. Cible le contrat du Dialogue
Forge tel que finalisé dans un lot parallèle (ne pas modifier ce contrat
depuis ce composant) : `POST /conversations` crée une conversation,
`POST /conversations/{id}/tours` streame du NDJSON (une ligne JSON par
événement : `{"type":"phrase","texte":...,"voix":...}` puis
`{"type":"fin","reponse":...}`), `POST /conversations/{id}/interrompre` et
`POST /conversations/{id}/clore` sont de simples appels ponctuels.
"""

import json
from collections.abc import AsyncIterator

import httpx

from app.dialogue.base import ClientDialogue, FinTour, Phrase


class ClientDialogueREST(ClientDialogue):
    """Client HTTP du Dialogue Forge."""

    def __init__(self, base_url: str) -> None:
        # Timeout de lecture généreux : le défaut httpx (5 s) tuait le stream
        # du premier tour à froid (prefill LLM ~13 s mesuré, cache de préfixe
        # vide — constaté au premier run réel, 2026-07-16). La cible ≤ 2 s est
        # une exigence produit, pas une affaire de timeout client.
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(10.0, read=120.0),
        )

    async def creer_conversation(self, persona: str | None = None) -> str:
        reponse = await self._client.post("/conversations", json={"persona": persona})
        reponse.raise_for_status()
        return reponse.json()["id"]

    async def jouer_tour(self, conversation: str, texte: str) -> AsyncIterator[Phrase | FinTour]:
        async with self._client.stream(
            "POST", f"/conversations/{conversation}/tours", json={"texte": texte}
        ) as reponse:
            reponse.raise_for_status()
            async for ligne in reponse.aiter_lines():
                if not ligne.strip():
                    continue
                evenement = json.loads(ligne)
                if evenement["type"] == "phrase":
                    yield Phrase(texte=evenement["texte"], voix=evenement["voix"])
                elif evenement["type"] == "fin":
                    yield FinTour(reponse=evenement["reponse"])

    async def interrompre(self, conversation: str, prefixe_prononce: str) -> None:
        reponse = await self._client.post(
            f"/conversations/{conversation}/interrompre",
            json={"prefixe": prefixe_prononce},
        )
        reponse.raise_for_status()

    async def clore(self, conversation: str) -> bool:
        reponse = await self._client.post(f"/conversations/{conversation}/clore")
        reponse.raise_for_status()
        return reponse.json()["episode_capture"]

    async def aclose(self) -> None:
        await self._client.aclose()
