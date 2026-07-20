import logging

from app.annonce.base import Annonceur

logger = logging.getLogger(__name__)


class AnnonceurJournal(Annonceur):
    """Annonceur factice : journalise et garde trace — tests et dev sans enceintes."""

    def __init__(self) -> None:
        self.dits: list[str] = []

    async def annoncer(self, texte: str) -> None:
        self.dits.append(texte)
        logger.info("ANNONCE : %s", texte)
