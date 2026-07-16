"""Le WAV de voice-forge doit être normalisé avant le helper Pipecat.

Constaté au premier run réel (2026-07-10, « ça grésille ») : voice-forge
(Chatterbox/torchaudio) renvoie du WAV **float32** (code de format 3) avec des
chunks additionnels (données à l'offset 80) — or le helper Pipecat
`_stream_audio_frames_from_iterator(strip_wav_header=True)` strippe 44 octets
fixes et suppose du PCM 16 bits. Le normaliseur réécrit le flux en WAV
canonique : en-tête de 44 octets, PCM 16 bits, rate d'origine préservé.
"""

import math
import struct

import pytest

from app.transport.normaliseur_wav import NormaliseurWavPCM16


def _wav_float32(rate: int, echantillons: list[float], chunks_annexes: bytes = b"") -> bytes:
    """Construit un WAV float32 mono minimal, avec chunks optionnels avant data."""
    donnees = struct.pack(f"<{len(echantillons)}f", *echantillons)
    fmt = struct.pack("<HHIIHH", 3, 1, rate, rate * 4, 4, 32)
    corps = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt
    corps += chunks_annexes
    corps += b"data" + struct.pack("<I", len(donnees)) + donnees
    return b"RIFF" + struct.pack("<I", len(corps)) + corps


def _wav_pcm16(rate: int, echantillons: list[int]) -> bytes:
    donnees = struct.pack(f"<{len(echantillons)}h", *echantillons)
    fmt = struct.pack("<HHIIHH", 1, 1, rate, rate * 2, 2, 16)
    corps = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt
    corps += b"data" + struct.pack("<I", len(donnees)) + donnees
    return b"RIFF" + struct.pack("<I", len(corps)) + corps


def _tout_avaler(normaliseur: NormaliseurWavPCM16, wav: bytes, taille_chunk: int) -> bytes:
    sortie = b""
    for i in range(0, len(wav), taille_chunk):
        sortie += normaliseur.avaler(wav[i : i + taille_chunk])
    return sortie + normaliseur.clore()


def _entete_et_donnees(sortie: bytes) -> tuple[bytes, bytes]:
    assert len(sortie) >= 44
    return sortie[:44], sortie[44:]


def test_le_float32_est_converti_en_pcm16_avec_entete_canonique():
    # Données à l'offset 80 comme le vrai voice-forge : 28 octets de chunks annexes.
    annexes = b"fact" + struct.pack("<I", 4) + b"\x00" * 4
    annexes += b"LIST" + struct.pack("<I", 8) + b"x" * 8
    wav = _wav_float32(24000, [0.0, 0.5, -0.5, 1.0, -1.0], chunks_annexes=annexes)
    sortie = _tout_avaler(NormaliseurWavPCM16(), wav, taille_chunk=7)

    entete, donnees = _entete_et_donnees(sortie)
    assert entete[:4] == b"RIFF" and entete[8:12] == b"WAVE"
    code, canaux, rate = struct.unpack("<HHI", entete[20:28])
    bits = struct.unpack("<H", entete[34:36])[0]
    assert (code, canaux, rate, bits) == (1, 1, 24000, 16)
    assert entete[36:40] == b"data"

    valeurs = struct.unpack("<5h", donnees)
    assert valeurs[0] == 0
    assert math.isclose(valeurs[1], 16383, abs_tol=1)
    assert math.isclose(valeurs[2], -16383, abs_tol=1)
    assert valeurs[3] == 32767  # 1.0 plafonné sans débordement
    assert valeurs[4] == -32767


def test_le_pcm16_passe_tel_quel_donnees_intactes():
    wav = _wav_pcm16(22050, [0, 1000, -1000, 32767])
    sortie = _tout_avaler(NormaliseurWavPCM16(), wav, taille_chunk=5)

    entete, donnees = _entete_et_donnees(sortie)
    rate = struct.unpack("<I", entete[24:28])[0]
    assert rate == 22050
    assert donnees == struct.pack("<4h", 0, 1000, -1000, 32767)


def test_un_echantillon_float32_coupe_entre_deux_chunks_est_reconstitue():
    wav = _wav_float32(24000, [0.25] * 9)
    # taille_chunk=3 : toutes les frontières tombent au milieu des float32.
    sortie = _tout_avaler(NormaliseurWavPCM16(), wav, taille_chunk=3)
    donnees = sortie[44:]
    assert len(donnees) == 9 * 2
    for (valeur,) in struct.iter_unpack("<h", donnees):
        assert math.isclose(valeur, 8191, abs_tol=1)


def test_un_format_non_gere_leve_une_erreur_claire():
    # PCM entier 32 bits (code 1, 32 bits) : ni float32, ni PCM16.
    donnees = struct.pack("<2i", 0, 1)
    fmt = struct.pack("<HHIIHH", 1, 1, 24000, 24000 * 4, 4, 32)
    corps = b"WAVE" + b"fmt " + struct.pack("<I", len(fmt)) + fmt
    corps += b"data" + struct.pack("<I", len(donnees)) + donnees
    wav = b"RIFF" + struct.pack("<I", len(corps)) + corps

    normaliseur = NormaliseurWavPCM16()
    with pytest.raises(ValueError, match="format WAV non géré"):
        _tout_avaler(normaliseur, wav, taille_chunk=64)
