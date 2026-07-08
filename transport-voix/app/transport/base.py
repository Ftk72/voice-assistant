"""Port de la couche transport temps réel (Pipecat/WebRTC)."""

from abc import ABC, abstractmethod


class Transport(ABC):
    """Établit la session temps réel avec la webview de la coquille (WebRTC) :
    pousse l'audio du micro vers le STT et rejoue l'audio produit par le TTS."""

    @abstractmethod
    async def demarrer(self) -> None:
        """Établit la session temps réel."""

    @abstractmethod
    async def arreter(self) -> None:
        """Termine la session temps réel."""
