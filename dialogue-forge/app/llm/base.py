"""Port du moteur LLM.

Le moteur produit un *flux* d'événements : des deltas de texte (la réponse au
fil de l'eau, pour la synthèse vocale phrase par phrase) et/ou des demandes
d'appel d'outil. Le format des messages et des définitions d'outils suit la
convention OpenAI (`role`/`content`, `tool_calls`/`tool`), afin de rester
compatible avec l'API de llama.cpp comme avec un éventuel autre backend.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

# Un message est un dict au format OpenAI : {"role": ..., "content": ...},
# éventuellement enrichi de "tool_calls" (assistant) ou "tool_call_id" (tool).
Message = dict[str, Any]

# Une définition d'outil au format OpenAI :
# {"type": "function", "function": {"name", "description", "parameters"}}.
DefinitionOutil = dict[str, Any]


@dataclass
class DeltaTexte:
    """Un fragment de texte de la réponse en cours."""

    texte: str


@dataclass
class AppelOutil:
    """Une demande d'appel d'outil émise par le LLM. `arguments` est la chaîne
    JSON brute produite par le modèle (décodée par l'orchestrateur)."""

    id: str
    nom: str
    arguments: str


# Un événement du flux : soit du texte, soit une demande d'outil.
EvenementLLM = DeltaTexte | AppelOutil


class MoteurLLM(ABC):
    """Port du moteur de génération. Un tour de génération produit un flux
    d'événements, terminé par l'épuisement de l'itérateur."""

    @abstractmethod
    def generer(
        self, messages: list[Message], outils: list[DefinitionOutil]
    ) -> AsyncIterator[EvenementLLM]:
        """Streame la génération pour `messages`, avec les `outils` disponibles.

        Convention respectée par les adaptateurs : un tour est *soit* du texte,
        *soit* des appels d'outils (jamais les deux entremêlés), ce qui autorise
        l'orchestrateur à diffuser les phrases dès qu'elles arrivent."""
        raise NotImplementedError
