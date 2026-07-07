"""Port de la mémoire (memory-forge vu par l'orchestrateur).

Deux gestes, cf. CONTEXT.md : l'**injection** (rechercher les faits pertinents
avant le tour) et l'**extraction** (capturer l'épisode après le tour).
"""

from abc import ABC, abstractmethod


class MoteurMemoire(ABC):
    @abstractmethod
    async def rechercher(self, question: str) -> list[str]:
        """Injection : les faits pertinents pour `question`, en texte simple."""

    @abstractmethod
    async def capturer_episode(self, contenu: str, nom: str) -> None:
        """Extraction : confie l'échange (`contenu`) à la mémoire pour intégration
        différée. `nom` identifie l'épisode (ici le persona du tour)."""
