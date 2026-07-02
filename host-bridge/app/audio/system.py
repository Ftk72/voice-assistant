"""Lecteur réel — jamais exécuté à ce jour (pattern GraphitiMemory).

Joue le wav sur les enceintes de l'hôte : sous Windows (la cible), directement
depuis la mémoire via `winsound` ; sous Linux (le dev), par un fichier temporaire
confié à `aplay`. Les imports plateforme restent dans la méthode.
"""

import subprocess
import sys
import tempfile

from app.audio.base import AudioPlayer


class SystemPlayer(AudioPlayer):
    def play_wav(self, data: bytes) -> None:
        if sys.platform.startswith("win"):
            import winsound

            winsound.PlaySound(data, winsound.SND_MEMORY)
            return
        with tempfile.NamedTemporaryFile(suffix=".wav") as file:
            file.write(data)
            file.flush()
            subprocess.run(["aplay", file.name])
