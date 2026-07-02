from abc import ABC, abstractmethod
from datetime import datetime

from app.schemas import Event, EventIn


class AgendaStore(ABC):
    """Port de l'agenda — le lieu unique des choses datées (CONTEXT.md § Agenda).
    Implémentation interchangeable sans toucher au serveur MCP ni à l'annonceur."""

    @abstractmethod
    async def add(self, event: EventIn) -> Event: ...

    @abstractmethod
    async def list_between(self, start: datetime, end: datetime) -> list[Event]:
        """Événements dont l'échéance tombe dans [start, end), triés par date."""

    @abstractmethod
    async def delete(self, event_id: str) -> bool:
        """True si l'événement existait."""

    @abstractmethod
    async def claim_due(self, now: datetime) -> list[Event]:
        """Événements dont l'heure d'annonce (échéance − préavis) est atteinte et
        pas encore annoncés ; les marque annoncés (une annonce ne part qu'une fois)."""
