from abc import ABC, abstractmethod

from app.schemas import CondenseGraphe


class GenerateurInsight(ABC):
    """Port du récit du graphe mémoire (ticket wayfinder 0020) : transforme un
    condensé statistique en un paragraphe français racontable oralement."""

    @abstractmethod
    async def generer(self, condense: CondenseGraphe) -> str:
        """Un seul paragraphe en français décrivant ce que la mémoire sait."""
