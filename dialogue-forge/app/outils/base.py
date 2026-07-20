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

    async def rafraichir(self) -> list[DefinitionOutil] | None:
        """Retente les forges tombées si le palier de reprise est écoulé.

        Concrète (pas abstraite) : les adaptateurs qui n'ont pas de notion de
        forge tombée (le factice, tout futur adaptateur simple) n'ont rien à
        implémenter — le comportement par défaut est « rien à rafraîchir ».

        Renvoie `None` quand rien n'a changé (chemin nominal), et le catalogue
        complet **seulement** quand une forge auparavant en échec vient de
        répondre à nouveau. Ce `None` compte : c'est le signal qui permet à
        l'orchestrateur de ne *pas* toucher au préfixe du prompt système envoyé
        au LLM (cf. docstring de module de `app/dialogue.py`) — invalider le
        cache de contexte de llama.cpp à chaque tour, pour rien, coûterait cher
        en latence sans qu'aucune forge n'ait réellement bougé."""
        return None
