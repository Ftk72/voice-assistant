from datetime import datetime, timedelta
from uuid import uuid4

from app.schemas import Event, EventIn
from app.store.base import AgendaStore


class InMemoryAgenda(AgendaStore):
    """Agenda factice pour les tests et le développement : rien ne survit au redémarrage."""

    def __init__(self) -> None:
        self._events: dict[str, Event] = {}

    async def add(self, event: EventIn) -> Event:
        stored = Event(id=uuid4().hex[:8], **event.model_dump())
        self._events[stored.id] = stored
        return stored

    async def list_between(self, start: datetime, end: datetime) -> list[Event]:
        selected = [e for e in self._events.values() if start <= e.when < end]
        return sorted(selected, key=lambda e: e.when)

    async def delete(self, event_id: str) -> bool:
        return self._events.pop(event_id, None) is not None

    async def claim_due(self, now: datetime) -> list[Event]:
        due = [
            event
            for event in self._events.values()
            if event.announce_lead_minutes is not None
            and event.announced_at is None
            and event.when - timedelta(minutes=event.announce_lead_minutes) <= now
        ]
        for event in due:
            event.announced_at = now
        return sorted(due, key=lambda e: e.when)
