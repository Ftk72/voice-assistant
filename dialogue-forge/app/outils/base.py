"""Port des outils (les forges vues comme fonctions appelables par le LLM).

L'orchestrateur expose au LLM les définitions au format OpenAI tools, puis
exécute les appels demandés et renvoie leur résultat textuel au LLM.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.llm.base import DefinitionOutil


class MoteurOutils(ABC):
    @abstractmethod
    async def lister_outils(self) -> list[DefinitionOutil]:
        """Les outils disponibles, au format OpenAI tools."""

    @abstractmethod
    async def appeler(self, nom: str, arguments: dict[str, Any]) -> str:
        """Exécute l'outil `nom` avec `arguments` (déjà décodés). Renvoie un
        résultat textuel, restitué tel quel au LLM."""
