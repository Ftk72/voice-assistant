import re
import shutil
from pathlib import Path

from app.schemas import Voice

# Lettres (accents inclus), chiffres, espace, apostrophe, tiret, underscore — jamais de
# séparateur de chemin ni de point : le nom devient un nom de dossier sous voices/.
VOICE_NAME_PATTERN = r"^[\w À-ÿ'-]{1,50}$"


class VoiceManager:
    """Découvre les voix déposées dans le dossier voices/.

    Une voix = un sous-dossier contenant au minimum un speaker.wav.
    Le scan se fait à chaque appel : une voix déposée est visible
    immédiatement, sans redémarrage.
    """

    def __init__(self, voices_dir: Path) -> None:
        self._voices_dir = voices_dir

    def speaker_wav(self, voice_id: str) -> Path | None:
        """Chemin de l'échantillon de référence de la voix, ou None si inconnue."""
        if not re.fullmatch(VOICE_NAME_PATTERN, voice_id):
            return None
        candidate = self._voices_dir / voice_id / "speaker.wav"
        return candidate if candidate.is_file() else None

    def create_voice(self, name: str, speaker_bytes: bytes) -> Voice:
        """Crée voices/name/speaker.wav. Lève FileExistsError si le nom est pris."""
        voice_dir = self._voices_dir / name
        if voice_dir.exists():
            raise FileExistsError(name)
        voice_dir.mkdir(parents=True)
        (voice_dir / "speaker.wav").write_bytes(speaker_bytes)
        return Voice(id=name, name=name)

    def delete_voice(self, voice_id: str) -> bool:
        """Supprime le dossier de la voix. False si la voix n'existe pas."""
        if self.speaker_wav(voice_id) is None:
            return False
        shutil.rmtree(self._voices_dir / voice_id)
        return True

    def list_voices(self) -> list[Voice]:
        if not self._voices_dir.is_dir():
            return []
        return sorted(
            (
                Voice(id=entry.name, name=entry.name)
                for entry in self._voices_dir.iterdir()
                if entry.is_dir() and (entry / "speaker.wav").is_file()
            ),
            key=lambda voice: voice.name,
        )
