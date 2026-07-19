"""Adaptateur réel : traduction et formulation par le LLM local compatible
OpenAI (llama.cpp, `llm_base_url`) — ticket wayfinder 0028.

**Exécuté au réel le 2026-07-19** (validation à l'œil du ticket 0028 sur le
corpus synthétique — budget ~18 s/question : deux appels, cf. ticket).

Même facture que `GenerateurInsightOpenAI` (0020) : client httpx direct, pas
de streaming, timeout large pour le premier appel (chargement des poids).
"""

import json
import re

import httpx

from app.interrogation.base import TraducteurQuestion
from app.interrogation.prompt import construire_messages_aiguillage, construire_messages_formulation
from app.schemas import Aiguillage, ContexteInterrogation


class TraducteurQuestionOpenAI(TraducteurQuestion):
    """Client HTTP direct (sans le SDK `openai`) de `POST /chat/completions` :
    température 0 (la traduction est une tâche déterministe, cf. le réglage
    d'extraction de graphiti.py)."""

    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=120.0)

    async def _completion(self, messages: list[dict[str, str]], max_tokens: int) -> str:
        reponse = await self._client.post(
            "/chat/completions",
            json={"messages": messages, "temperature": 0, "max_tokens": max_tokens},
        )
        reponse.raise_for_status()
        return reponse.json()["choices"][0]["message"]["content"].strip()

    async def aiguiller(
        self, question: str, contexte: ContexteInterrogation | None = None
    ) -> Aiguillage:
        contenu = await self._completion(
            construire_messages_aiguillage(question, contexte), max_tokens=300
        )
        # Le modèle peut envelopper le JSON (` ```json `, prose…) : on extrait
        # le premier objet complet plutôt que d'échouer sur l'emballage.
        bloc = re.search(r"\{.*\}", contenu, flags=re.DOTALL)
        if bloc is None:
            raise ValueError(f"aiguillage sans JSON : {contenu!r}")
        return Aiguillage.model_validate(json.loads(bloc.group()))

    async def formuler(self, question: str, resultats: list[dict]) -> str:
        return await self._completion(
            construire_messages_formulation(question, resultats), max_tokens=400
        )

    async def aclose(self) -> None:
        await self._client.aclose()
