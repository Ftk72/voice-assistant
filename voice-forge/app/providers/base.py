from abc import ABC, abstractmethod
from pathlib import Path


class BaseTTSProvider(ABC):
    """Moteur de synthèse interchangeable. Changer de provider ne touche jamais OpenWebUI."""

    media_type: str

    @abstractmethod
    def synthesize(self, text: str, speaker_wav: Path) -> bytes:
        """Synthétise `text` avec la voix de référence `speaker_wav`, renvoie l'audio encodé."""
