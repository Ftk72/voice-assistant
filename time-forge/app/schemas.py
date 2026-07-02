from datetime import datetime

from pydantic import BaseModel


class EventIn(BaseModel):
    """Une entrée datée de l'agenda (CONTEXT.md § Agenda). Le rappel est un événement
    dont l'annonce est la raison d'être : announce_lead_minutes=0."""

    title: str
    when: datetime
    # None : événement purement consultatif, jamais annoncé.
    announce_lead_minutes: int | None = None


class Event(EventIn):
    id: str
    announced_at: datetime | None = None


class Timer(BaseModel):
    """Compte à rebours éphémère, précis à la seconde — hors agenda (CONTEXT.md)."""

    label: str
    ends_at: datetime
