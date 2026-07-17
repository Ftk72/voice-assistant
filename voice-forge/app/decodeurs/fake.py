from app.decodeurs.base import DecodeurAudio, FormatAudioNonSupporte


class DecodeurFactice(DecodeurAudio):
    """Défaut, zéro système : aucun décodage. Un build sans ffmpeg n'accepte que le WAV.

    Refuse donc tout non-WAV — l'atelier reste fonctionnel sur le seul WAV,
    et le multi-format n'existe qu'avec l'adaptateur réel (ffmpeg).
    """

    def en_wav(self, donnees: bytes) -> bytes:
        raise FormatAudioNonSupporte("Aucun décodeur audio disponible (build sans ffmpeg).")
