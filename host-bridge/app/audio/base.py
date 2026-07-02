from abc import ABC, abstractmethod


class AudioPlayer(ABC):
    """Port du lecteur audio : joue sur les enceintes de l'hôte un wav déjà
    synthétisé (le Pont reste sans intelligence — la voix vient du Voice Forge,
    via le Time Forge, ADR 0008)."""

    @abstractmethod
    def play_wav(self, data: bytes) -> None: ...
