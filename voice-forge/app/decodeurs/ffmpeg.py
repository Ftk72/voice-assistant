import subprocess

from app.decodeurs.base import DecodeurAudio, FormatAudioNonSupporte


class DecodeurFfmpeg(DecodeurAudio):
    """Adaptateur réel : ffmpeg en sous-processus, entrée/sortie par tubes.

    Décode n'importe quel conteneur (mp3, m4a, ogg, flac…) en WAV PCM16 mono,
    rééchantillonné à `frequence` — un échantillon de référence propre pour le
    clonage. **Validé au réel le 2026-07-17** : un mp3 déposé via /admin est
    décodé et enrôlé (ffmpeg présent dans l'image). Reste non confirmé : que le
    format cible (24 kHz mono) corresponde à ce qu'attend Chatterbox — l'aperçu
    audible (clonage réel) n'a pas encore été exercé (ticket 0012) ; sinon un
    clone issu d'un mp3 pourrait diverger d'un clone issu d'un WAV déposé tel quel.
    """

    def __init__(self, binaire: str = "ffmpeg", frequence: int = 24_000) -> None:
        self._binaire = binaire
        self._frequence = frequence

    def en_wav(self, donnees: bytes) -> bytes:
        commande = [
            self._binaire,
            "-hide_banner",
            "-loglevel",
            "error",
            "-i",
            "pipe:0",
            "-ac",
            "1",
            "-ar",
            str(self._frequence),
            "-c:a",
            "pcm_s16le",
            "-f",
            "wav",
            "pipe:1",
        ]
        try:
            resultat = subprocess.run(commande, input=donnees, capture_output=True, check=True)
        except FileNotFoundError as erreur:
            raise FormatAudioNonSupporte("ffmpeg introuvable dans l'image.") from erreur
        except subprocess.CalledProcessError as erreur:
            details = erreur.stderr.decode(errors="replace")[:200] if erreur.stderr else ""
            raise FormatAudioNonSupporte(
                f"ffmpeg n'a pas pu décoder l'entrée : {details}"
            ) from erreur
        # Un code retour 0 avec une sortie vide ou non-WAV stockerait un speaker.wav
        # inutilisable : on refuse plutôt que d'enrôler une voix silencieuse.
        if resultat.stdout[0:4] != b"RIFF" or resultat.stdout[8:12] != b"WAVE":
            raise FormatAudioNonSupporte("ffmpeg n'a produit aucun WAV exploitable.")
        return resultat.stdout
