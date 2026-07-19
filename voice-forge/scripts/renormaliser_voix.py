"""Re-normalise en place les speaker.wav déjà enrôlés (ticket wayfinder 0023).

Les voix enrôlées avant la normalisation à l'enrôlement gardent leur niveau
d'origine (Jackie : crête -11,7 dBFS → clone faible). Ce script leur applique
la même normalisation que `VoiceManager.create_voice`, avec sauvegarde de
l'original en `speaker.avant-0023.wav` à côté.

Usage (dans le conteneur, qui voit /data/voices) :
    docker compose exec voice-forge uv run --no-sync python scripts/renormaliser_voix.py
Ou en local :
    uv run python scripts/renormaliser_voix.py ../voices
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.voices.normalisation import normaliser_wav_pcm16  # noqa: E402


def renormaliser(voices_dir: Path) -> None:
    for dossier in sorted(voices_dir.iterdir()):
        wav = dossier / "speaker.wav"
        if not wav.is_file():
            continue
        avant = wav.read_bytes()
        apres = normaliser_wav_pcm16(avant)
        if apres == avant:
            print(f"{dossier.name}: inchangé")
            continue
        (dossier / "speaker.avant-0023.wav").write_bytes(avant)
        wav.write_bytes(apres)
        print(f"{dossier.name}: normalisé ({len(avant)} → {len(apres)} octets)")


if __name__ == "__main__":
    cible = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/data/voices")
    renormaliser(cible)
