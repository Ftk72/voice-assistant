from abc import ABC, abstractmethod


class Annonceur(ABC):
    """Port de l'annonceur — le seul canal de parole spontanée de l'assistant
    (ADR 0008) : la fin d'une Tâche s'annonce comme l'échéance d'un minuteur,
    hors annonce l'assistant ne parle jamais sans qu'on lui parle."""

    @abstractmethod
    async def annoncer(self, texte: str) -> None: ...
