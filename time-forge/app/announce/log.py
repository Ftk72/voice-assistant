import logging

from app.announce.base import Announcer

logger = logging.getLogger(__name__)


class LogAnnouncer(Announcer):
    """Annonceur factice : journalise et garde trace — tests et dev sans enceintes."""

    def __init__(self) -> None:
        self.spoken: list[str] = []

    async def announce(self, text: str) -> None:
        self.spoken.append(text)
        logger.info("ANNONCE : %s", text)
