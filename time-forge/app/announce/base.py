from abc import ABC, abstractmethod


class Announcer(ABC):
    """Port de l'annonceur — le seul canal de parole spontanée de l'assistant
    (CONTEXT.md § Quotidien) : hors annonce, l'assistant ne parle jamais sans
    qu'on lui parle."""

    @abstractmethod
    async def announce(self, text: str) -> None: ...
