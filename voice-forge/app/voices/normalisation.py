"""Normalisation de niveau du speaker.wav à l'enrôlement (ticket wayfinder 0023).

Chatterbox recopie le niveau de l'échantillon de référence : une référence
faible donne un clone faible (mesuré : Jackie crête -11,7 dBFS → synthèses
~-12 dB sous les autres voix). On ramène chaque référence à un RMS cible,
borné par un plafond de crête pour ne jamais écrêter.

Python pur (stdlib wave) : s'applique aussi aux builds sans ffmpeg. La
réécriture produit un en-tête sain — les WAV décodés par ffmpeg sur tube
portent des tailles RIFF/data à 0xFFFFFFFF.

Meilleur-effort : tout contenu non lisible comme WAV PCM 16 bits ressort tel
quel — la normalisation ne refuse jamais un enrôlement.
"""

import array
import io
import math
import wave

RMS_CIBLE_DBFS = -20.0
CRETE_PLAFOND_DBFS = -1.0


def normaliser_wav_pcm16(donnees: bytes) -> bytes:
    """Ramène un WAV PCM16 au RMS cible sans dépasser le plafond de crête."""
    try:
        with wave.open(io.BytesIO(donnees)) as entree:
            if entree.getsampwidth() != 2:
                return donnees
            canaux = entree.getnchannels()
            frequence = entree.getframerate()
            echantillons = array.array("h", entree.readframes(entree.getnframes()))
    except (wave.Error, EOFError, ValueError):
        return donnees

    if not echantillons:
        return donnees
    crete = max(abs(valeur) for valeur in echantillons)
    if crete == 0:
        return donnees
    rms = math.sqrt(sum(valeur * valeur for valeur in echantillons) / len(echantillons))

    gain_rms = 32768 * 10 ** (RMS_CIBLE_DBFS / 20) / rms
    gain_plafond = 32768 * 10 ** (CRETE_PLAFOND_DBFS / 20) / crete
    gain = min(gain_rms, gain_plafond)

    amplifies = array.array(
        "h",
        (max(-32768, min(32767, round(valeur * gain))) for valeur in echantillons),
    )
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as sortie:
        sortie.setnchannels(canaux)
        sortie.setsampwidth(2)
        sortie.setframerate(frequence)
        sortie.writeframes(amplifies.tobytes())
    return tampon.getvalue()
