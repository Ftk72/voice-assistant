"""Agenda persistant en SQLite (stdlib — aucune dépendance) : l'agenda doit
survivre aux redémarrages, contrairement aux minuteurs."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from app.schemas import Event, EventIn
from app.store.base import AgendaStore

_SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    when_at TEXT NOT NULL,               -- ISO 8601, heure locale du conteneur (TZ)
    announce_lead_minutes INTEGER,       -- NULL : jamais annoncé
    announced_at TEXT
);
"""


class SqliteAgenda(AgendaStore):
    def __init__(self, path: Path) -> None:
        # Un seul worker uvicorn ; les opérations sont courtes (pas de to_thread).
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute(_SCHEMA)
        self._db.commit()

    async def add(self, event: EventIn) -> Event:
        stored = Event(id=uuid4().hex[:8], **event.model_dump())
        self._db.execute(
            "INSERT INTO events (id, title, when_at, announce_lead_minutes) VALUES (?, ?, ?, ?)",
            (stored.id, stored.title, stored.when.isoformat(), stored.announce_lead_minutes),
        )
        self._db.commit()
        return stored

    async def list_between(self, start: datetime, end: datetime) -> list[Event]:
        rows = self._db.execute(
            "SELECT * FROM events WHERE when_at >= ? AND when_at < ? ORDER BY when_at",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return [_to_event(row) for row in rows]

    async def delete(self, event_id: str) -> bool:
        cursor = self._db.execute("DELETE FROM events WHERE id = ?", (event_id,))
        self._db.commit()
        return cursor.rowcount > 0

    async def claim_due(self, now: datetime) -> list[Event]:
        rows = self._db.execute(
            "SELECT * FROM events WHERE announce_lead_minutes IS NOT NULL "
            "AND announced_at IS NULL ORDER BY when_at",
        ).fetchall()
        # Le calcul échéance − préavis se fait en Python : dates ISO, pas d'arithmétique SQL.
        due = [
            event
            for event in map(_to_event, rows)
            if event.when - timedelta(minutes=event.announce_lead_minutes or 0) <= now
        ]
        for event in due:
            event.announced_at = now
            self._db.execute(
                "UPDATE events SET announced_at = ? WHERE id = ?",
                (now.isoformat(), event.id),
            )
        self._db.commit()
        return due


def _to_event(row: sqlite3.Row) -> Event:
    return Event(
        id=row["id"],
        title=row["title"],
        when=datetime.fromisoformat(row["when_at"]),
        announce_lead_minutes=row["announce_lead_minutes"],
        announced_at=(
            datetime.fromisoformat(row["announced_at"]) if row["announced_at"] else None
        ),
    )
