"""Port du moteur STT (reconnaissance vocale)."""

from abc import ABC, abstractmethod


class MoteurSTT(ABC):
    """Port de la transcription audio → texte.

    whisper.cpp est un moteur **batch** : pas de transcription partielle au
    fil de l'eau, on lui passe un segment audio complet et on récupère le
    texte final en un coup."""

    @abstractmethod
    async def transcrire(self, audio: bytes, *, langue: str = "fr") -> str:
        """Transcrit `audio` (segment complet) en texte, dans `langue`."""
