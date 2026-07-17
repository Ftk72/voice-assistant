from abc import ABC, abstractmethod


class FormatAudioNonSupporte(Exception):
    """L'entrée n'a pas pu être décodée en WAV (format inconnu, ou aucun décodeur)."""


class DecodeurAudio(ABC):
    """Convertit un conteneur audio quelconque en WAV, pour l'échantillon de référence.

    Le chemin WAV nominal ne passe jamais ici : l'appelant stocke un WAV tel quel
    et ne sollicite un décodeur que pour les autres formats (mp3, m4a, ogg, flac…).
    """

    @abstractmethod
    def en_wav(self, donnees: bytes) -> bytes:
        """Décode `donnees` en WAV PCM16 mono, ou lève FormatAudioNonSupporte."""
