"""
title: Mémoire persistante (Memory Forge)
author: voice-assistant
version: 0.1.0
description: Injecte les souvenirs pertinents avant chaque génération (inlet) et capture
             les échanges vers le Memory Forge (outlet). Fail-open — si le Memory Forge
             est indisponible, la conversation continue sans mémoire.
             Persona off-record = ne pas activer cette Filter sur ce modèle.
"""

import contextlib
from datetime import UTC, datetime

from pydantic import BaseModel, Field

MEMORY_HEADER = "Ce que ta mémoire sait déjà (faits datés, à évoquer naturellement si pertinent) :"


class Filter:
    class Valves(BaseModel):
        memory_forge_url: str = Field(
            default="http://memory:8200",
            description="URL du Memory Forge (réseau Docker interne)",
        )
        top_k: int = Field(default=5, description="Nombre maximum de faits injectés")
        search_timeout_ms: int = Field(
            default=300,
            description="Budget latence de l'injection (au-delà : fail-open, pas de mémoire)",
        )
        enabled: bool = Field(default=True, description="Activer la mémoire")

    def __init__(self):
        self.valves = self.Valves()

    async def inlet(self, body: dict, __user__: dict | None = None) -> dict:
        if not self.valves.enabled:
            return body
        messages = body.get("messages", [])
        query = self._last_content(messages, role="user")
        if not query:
            return body
        try:
            facts = await self._search(query)
        except Exception:
            return body  # fail-open : jamais de panne visible côté conversation
        if facts:
            block = "\n".join(f"- {fact['text']}" for fact in facts[: self.valves.top_k])
            self._prepend_system(messages, f"{MEMORY_HEADER}\n{block}")
        return body

    async def outlet(self, body: dict, __user__: dict | None = None) -> dict:
        if not self.valves.enabled:
            return body
        messages = body.get("messages", [])
        user_text = self._last_content(messages, role="user")
        assistant_text = self._last_content(messages, role="assistant")
        if not user_text or not assistant_text:
            return body
        content = f"Utilisateur : {user_text}\nAssistant : {assistant_text}"
        name = f"conversation {body.get('chat_id', datetime.now(UTC).date().isoformat())}"
        # La capture ne doit jamais casser la réponse.
        with contextlib.suppress(Exception):
            await self._send_episode(content, name)
        return body

    # ---- helpers ----

    @staticmethod
    def _last_content(messages: list[dict], role: str) -> str:
        for message in reversed(messages):
            if message.get("role") == role and isinstance(message.get("content"), str):
                return message["content"]
        return ""

    @staticmethod
    def _prepend_system(messages: list[dict], text: str) -> None:
        for message in messages:
            if message.get("role") == "system":
                message["content"] = f"{message['content']}\n\n{text}"
                return
        messages.insert(0, {"role": "system", "content": text})

    async def _search(self, query: str) -> list[dict]:
        import aiohttp

        timeout = aiohttp.ClientTimeout(total=self.valves.search_timeout_ms / 1000)
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.get(
                f"{self.valves.memory_forge_url}/search", params={"q": query}
            ) as response,
        ):
            response.raise_for_status()
            return (await response.json())["facts"]

    async def _send_episode(self, content: str, name: str) -> None:
        import aiohttp

        timeout = aiohttp.ClientTimeout(total=5)
        async with (
            aiohttp.ClientSession(timeout=timeout) as session,
            session.post(
                f"{self.valves.memory_forge_url}/episodes",
                json={"content": content, "source": "conversation", "name": name},
            ) as response,
        ):
            response.raise_for_status()
