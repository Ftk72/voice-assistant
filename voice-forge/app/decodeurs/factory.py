from app.config import Settings
from app.decodeurs.base import DecodeurAudio
from app.decodeurs.fake import DecodeurFactice
from app.decodeurs.ffmpeg import DecodeurFfmpeg


def build_decodeur(settings: Settings) -> DecodeurAudio:
    if settings.decodeur == "ffmpeg":
        return DecodeurFfmpeg()
    return DecodeurFactice()
