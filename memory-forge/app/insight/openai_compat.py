"""Adaptateur réel : récit du graphe mémoire par un LLM compatible OpenAI
(llama.cpp, `llm_base_url`) — ticket wayfinder 0020.

**Exécuté au réel le 2026-07-18** (smoke-test WSL → port debug 8001, Qwen3.6) :
paragraphe français correct, 93 s au premier appel (chargement des poids),
9,1 s en régime. Aucun test automatisé ne l'instancie ni ne le joint (zéro
réseau dans la suite). Pas de streaming (contrairement au moteur de
dialogue-forge) : un seul paragraphe suffit, la réponse complète est attendue.
Timeout large (120 s) à cause du premier appel.
"""

import httpx

from app.insight.base import GenerateurInsight
from app.insight.prompt import construire_messages
from app.schemas import CondenseGraphe


class GenerateurInsightOpenAI(GenerateurInsight):
    """Client HTTP direct (sans le SDK `openai`) de `POST /chat/completions`."""

    def __init__(self, base_url: str) -> None:
        self._client = httpx.AsyncClient(base_url=base_url, timeout=120.0)

    async def generer(self, condense: CondenseGraphe) -> str:
        corps = {
            "messages": construire_messages(condense),
            "temperature": 0.3,
            "max_tokens": 400,
        }
        reponse = await self._client.post("/chat/completions", json=corps)
        reponse.raise_for_status()
        contenu = reponse.json()["choices"][0]["message"]["content"]
        return contenu.strip()

    async def aclose(self) -> None:
        await self._client.aclose()
