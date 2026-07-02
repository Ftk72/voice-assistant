"""Les minuteurs : éphémères, hors agenda, précis à la seconde (CONTEXT.md).
Une tâche asyncio par minuteur — pas de polling, pas de persistance : un
redémarrage du service les perd, assumé pour un compte à rebours de cuisine."""

import asyncio
from datetime import datetime, timedelta

from app.announce.base import Announcer
from app.schemas import Timer


class TimerBoard:
    def __init__(self, announcer: Announcer) -> None:
        self._announcer = announcer
        self._tasks: dict[str, asyncio.Task] = {}
        self._timers: dict[str, Timer] = {}

    def start(self, label: str, seconds: int) -> Timer:
        """Écrase un minuteur existant de même étiquette (« remets le minuteur pâtes »)."""
        self.cancel(label)
        timer = Timer(label=label, ends_at=datetime.now() + timedelta(seconds=seconds))
        self._timers[label] = timer
        self._tasks[label] = asyncio.get_running_loop().create_task(self._ring(label, seconds))
        return timer

    def cancel(self, label: str) -> bool:
        task = self._tasks.pop(label, None)
        self._timers.pop(label, None)
        if task is None:
            return False
        task.cancel()
        return True

    def active(self) -> list[Timer]:
        return sorted(self._timers.values(), key=lambda t: t.ends_at)

    def shutdown(self) -> None:
        for label in list(self._tasks):
            self.cancel(label)

    async def _ring(self, label: str, seconds: int) -> None:
        await asyncio.sleep(seconds)
        # Le minuteur ne survit pas à son échéance (CONTEXT.md).
        self._timers.pop(label, None)
        self._tasks.pop(label, None)
        await self._announcer.announce(f"Le minuteur « {label} » est terminé.")
