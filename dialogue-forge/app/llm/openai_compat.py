"""Adaptateur LLM réel : streaming vers une API compatible OpenAI (llama.cpp).

**Validé en réel le 2026-07-07** contre llama.cpp (`llm_base_url`), avec et
sans outils. Aucun test ne l'instancie ni ne le joint (zéro réseau dans la
suite automatisée). Volontairement sans le SDK `openai` : on parle directement
à `POST /chat/completions` (stream SSE) avec le client HTTP du dépôt (httpx).
"""

import json
from collections.abc import AsyncIterator

import httpx

from app.config import Settings
from app.llm.base import (
    AppelOutil,
    DefinitionOutil,
    DeltaTexte,
    EvenementLLM,
    Message,
    MoteurLLM,
)


class MoteurLLMOpenAI(MoteurLLM):
    """Client streaming de l'API chat/completions compatible OpenAI."""

    def __init__(self, settings: Settings) -> None:
        self._model = settings.llm_model
        self._client = httpx.AsyncClient(
            base_url=settings.llm_base_url,
            timeout=httpx.Timeout(300.0, connect=10.0),
        )

    async def generer(
        self, messages: list[Message], outils: list[DefinitionOutil]
    ) -> AsyncIterator[EvenementLLM]:
        corps: dict = {"model": self._model, "messages": messages, "stream": True}
        if outils:
            corps["tools"] = outils

        # Accumulateur des appels d'outils, indexés comme le fait l'API OpenAI :
        # les deltas arrivent morceau par morceau (nom puis arguments).
        appels: dict[int, dict] = {}

        async with self._client.stream("POST", "/chat/completions", json=corps) as reponse:
            reponse.raise_for_status()
            async for ligne in reponse.aiter_lines():
                if not ligne.startswith("data:"):
                    continue
                donnees = ligne[len("data:") :].strip()
                if donnees == "[DONE]":
                    break
                delta = json.loads(donnees)["choices"][0]["delta"]
                if delta.get("content"):
                    yield DeltaTexte(delta["content"])
                for appel_delta in delta.get("tool_calls", []):
                    index = appel_delta.get("index", 0)
                    accumule = appels.setdefault(
                        index, {"id": "", "nom": "", "arguments": ""}
                    )
                    if appel_delta.get("id"):
                        accumule["id"] = appel_delta["id"]
                    fonction = appel_delta.get("function", {})
                    if fonction.get("name"):
                        accumule["nom"] = fonction["name"]
                    if fonction.get("arguments"):
                        accumule["arguments"] += fonction["arguments"]

        for index in sorted(appels):
            appel = appels[index]
            yield AppelOutil(
                id=appel["id"] or f"appel-{index}",
                nom=appel["nom"],
                arguments=appel["arguments"],
            )

    async def aclose(self) -> None:
        await self._client.aclose()
