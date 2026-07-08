"""Port du moteur TTS (synthèse vocale)."""

from abc import ABC, abstractmethod


class MoteurTTS(ABC):
    """Port de la synthèse texte → audio."""

    @abstractmethod
    async def synthetiser(self, texte: str, *, voix: str) -> bytes:
        """Synthétise `texte` avec `voix`, renvoie l'audio en octets."""
