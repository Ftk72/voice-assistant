"""Adaptateur outils réel : client MCP streamable HTTP, agrégeant plusieurs forges.

**Validé en réel le 2026-07-07** contre les serveurs MCP de time-, world- et
memory-forge (listage agrégé et appel routé, notamment `weather` du
world-forge). Aucun test ne l'instancie ni ne le joint (zéro réseau dans la
suite automatisée).

Le forge est *client* MCP (écart assumé : il n'expose aucun serveur MCP). On
ouvre une session par URL à la demande, on agrège les outils de tous les
serveurs et on convertit chaque outil MCP vers le format OpenAI tools ; les
appels sont routés vers le serveur propriétaire de l'outil.
"""

import json
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.llm.base import DefinitionOutil
from app.outils.base import MoteurOutils


def _vers_format_openai(nom: str, description: str | None, schema: dict) -> DefinitionOutil:
    return {
        "type": "function",
        "function": {
            "name": nom,
            "description": description or "",
            "parameters": schema or {"type": "object", "properties": {}},
        },
    }


class OutilsMCP(MoteurOutils):
    def __init__(self, urls: list[str]) -> None:
        self._urls = urls
        # nom d'outil → URL du serveur qui le porte (peuplé par lister_outils).
        self._routage: dict[str, str] = {}

    async def lister_outils(self) -> list[DefinitionOutil]:
        definitions: list[DefinitionOutil] = []
        self._routage.clear()
        for url in self._urls:
            async with (
                streamablehttp_client(url) as (lecture, ecriture, _),
                ClientSession(lecture, ecriture) as session,
            ):
                await session.initialize()
                for outil in (await session.list_tools()).tools:
                    self._routage[outil.name] = url
                    definitions.append(
                        _vers_format_openai(outil.name, outil.description, outil.inputSchema)
                    )
        return definitions

    async def appeler(self, nom: str, arguments: dict[str, Any]) -> str:
        url = self._routage.get(nom)
        if url is None:
            return f"Outil inconnu : {nom}"
        async with (
            streamablehttp_client(url) as (lecture, ecriture, _),
            ClientSession(lecture, ecriture) as session,
        ):
            await session.initialize()
            resultat = await session.call_tool(nom, arguments)
        morceaux = [
            bloc.text for bloc in resultat.content if getattr(bloc, "type", None) == "text"
        ]
        return "\n".join(morceaux) if morceaux else json.dumps(
            [bloc.model_dump() for bloc in resultat.content], ensure_ascii=False
        )
