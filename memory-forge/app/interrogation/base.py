from abc import ABC, abstractmethod

from app.schemas import Aiguillage, ContexteInterrogation


class TraducteurQuestion(ABC):
    """Port de la traduction français → requête (ticket wayfinder 0028, modèle
    LinkQ) : un seul appel structuré pour l'aiguillage (gabarit ou Cypher
    libre), un second pour formuler la réponse depuis les résultats
    vérité-terrain — jamais depuis la tête du LLM."""

    @abstractmethod
    async def aiguiller(
        self, question: str, contexte: ContexteInterrogation | None = None
    ) -> Aiguillage:
        """Le JSON du monologue intérieur : mentions d'entités, et soit
        `{gabarit, parametres}`, soit `{cypher}` (repli libre)."""

    @abstractmethod
    async def formuler(self, question: str, resultats: list[dict]) -> str:
        """Une réponse française nourrie exclusivement des résultats fournis."""
