"""Normalisation du speaker.wav à l'enrôlement (ticket wayfinder 0023).

Constat mesuré : Chatterbox recopie le niveau de l'échantillon de référence —
une référence faible (Jackie, crête -11,7 dBFS, RMS -29,9 dBFS) donne un clone
faible. La normalisation vise un RMS cible avec plafond de crête, en Python pur
(stdlib wave), et réécrit au passage un en-tête sain (les WAV issus du décodage
ffmpeg par tube portent des tailles RIFF/data à 0xFFFFFFFF).
"""

import array
import io
import math
import wave

from app.voices.normalisation import CRETE_PLAFOND_DBFS, RMS_CIBLE_DBFS, normaliser_wav_pcm16


def _wav_pcm16(echantillons: list[int], frequence: int = 24_000, canaux: int = 1) -> bytes:
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as sortie:
        sortie.setnchannels(canaux)
        sortie.setsampwidth(2)
        sortie.setframerate(frequence)
        sortie.writeframes(array.array("h", echantillons).tobytes())
    return tampon.getvalue()


def _mesures(wav: bytes) -> tuple[float, float]:
    """(crête, RMS) en dBFS du WAV PCM16 donné."""
    with wave.open(io.BytesIO(wav)) as entree:
        echantillons = array.array("h", entree.readframes(entree.getnframes()))
    crete = max(abs(valeur) for valeur in echantillons)
    rms = math.sqrt(sum(valeur * valeur for valeur in echantillons) / len(echantillons))
    return 20 * math.log10(crete / 32768), 20 * math.log10(rms / 32768)


def _sinusoide(amplitude: int, nombre: int = 24_000) -> list[int]:
    return [round(amplitude * math.sin(2 * math.pi * 440 * i / 24_000)) for i in range(nombre)]


def test_une_voix_faible_remonte_au_rms_cible():
    wav = _wav_pcm16(_sinusoide(amplitude=1000))
    crete, rms = _mesures(normaliser_wav_pcm16(wav))
    assert abs(rms - RMS_CIBLE_DBFS) < 0.5
    assert crete <= CRETE_PLAFOND_DBFS + 0.1


def test_le_plafond_de_crete_borne_le_gain():
    # Crête-RMS énorme (une pointe isolée sur un fond très faible, façon Jackie) :
    # viser le RMS cible sans plafond écrêterait la pointe.
    echantillons = _sinusoide(amplitude=100)
    echantillons[100] = 20_000
    crete, rms = _mesures(normaliser_wav_pcm16(_wav_pcm16(echantillons)))
    assert crete <= CRETE_PLAFOND_DBFS + 0.1
    assert rms < RMS_CIBLE_DBFS  # le plafond a bridé le gain, sans écrêtage

def test_une_voix_forte_est_attenuee_vers_le_rms_cible():
    wav = _wav_pcm16(_sinusoide(amplitude=30_000))
    _, rms = _mesures(normaliser_wav_pcm16(wav))
    assert abs(rms - RMS_CIBLE_DBFS) < 0.5


def test_l_en_tete_streaming_ffmpeg_est_reecrit_sain():
    # ffmpeg sur pipe:1 ne peut pas revenir écrire les tailles : RIFF/data à 0xFFFFFFFF.
    wav = bytearray(_wav_pcm16(_sinusoide(amplitude=1000)))
    wav[4:8] = b"\xff\xff\xff\xff"
    wav[40:44] = b"\xff\xff\xff\xff"
    normalise = normaliser_wav_pcm16(bytes(wav))
    with wave.open(io.BytesIO(normalise)) as sortie:
        assert sortie.getnframes() == 24_000
        assert sortie.getframerate() == 24_000


def test_le_silence_ressort_inchange():
    wav = _wav_pcm16([0] * 1000)
    assert normaliser_wav_pcm16(wav) == wav


def test_un_wav_non_pcm16_ressort_inchange():
    # Dépôt WAV direct exotique (float32…) : la normalisation est un meilleur-effort,
    # jamais un refus — le fichier passe tel quel.
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as sortie:
        sortie.setnchannels(1)
        sortie.setsampwidth(4)
        sortie.setframerate(24_000)
        sortie.writeframes(b"\x00" * 400)
    wav = tampon.getvalue()
    assert normaliser_wav_pcm16(wav) == wav


def test_un_contenu_non_wav_ressort_inchange():
    assert normaliser_wav_pcm16(b"pas un wav du tout") == b"pas un wav du tout"


def test_le_stereo_garde_ses_canaux_et_sa_frequence():
    gauche_droite = []
    for valeur in _sinusoide(amplitude=1000, nombre=4800):
        gauche_droite += [valeur, valeur // 2]
    wav = _wav_pcm16(gauche_droite, frequence=48_000, canaux=2)
    with wave.open(io.BytesIO(normaliser_wav_pcm16(wav))) as sortie:
        assert sortie.getnchannels() == 2
        assert sortie.getframerate() == 48_000
