"""Adaptateur réel : une complétion non streamée vers une API compatible
OpenAI (llama.cpp). **Validé en réel le 2026-07-20** (prototype HITL du
ticket 0034 : 3/3 Tâches françaises réussies contre le LLM local). Aucun test
ne l'instancie ni ne le joint (zéro réseau dans la suite automatisée)."""

import httpx

from app.config import Settings
from app.llm.base import Message, MoteurLLM


class MoteurLLMOpenAI(MoteurLLM):
    """Client non streamé de l'API chat/completions compatible OpenAI."""

    def __init__(self, settings: Settings) -> None:
        self._model = settings.llm_model
        self._client = httpx.AsyncClient(
            base_url=settings.llm_base_url,
            timeout=httpx.Timeout(300.0, connect=10.0),
        )

    async def completer(self, messages: list[Message]) -> str:
        reponse = await self._client.post(
            "/chat/completions",
            json={"model": self._model, "messages": messages, "stream": False},
        )
        reponse.raise_for_status()
        return reponse.json()["choices"][0]["message"]["content"]

    async def aclose(self) -> None:
        await self._client.aclose()
