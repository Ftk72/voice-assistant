"""Normalisation du flux WAV de voice-forge vers un WAV canonique PCM 16 bits.

Constaté au premier run réel (2026-07-10) : voice-forge (Chatterbox via
torchaudio) renvoie du WAV **float32** (code de format 3) dont le chunk `data`
commence à l'offset 80 (chunks annexes entre `fmt ` et `data`). Le helper
Pipecat `_stream_audio_frames_from_iterator(strip_wav_header=True)` strippe
44 octets fixes et suppose du PCM 16 bits : il jouait donc 36 octets d'en-tête
comme du son puis chaque float32 comme deux échantillons int16 — le
grésillement entendu.

Ce normaliseur, **sans aucune dépendance Pipecat** (testable sans l'extra),
réécrit le flux au fil de l'eau : en-tête canonique de 44 octets (PCM 16 bits,
mono, rate d'origine), données converties float32 → int16 si besoin. Un WAV
déjà en PCM 16 bits ressort avec ses données intactes. Le résultat se donne
tel quel au helper Pipecat (qui n'y lit que le rate et strippe 44 octets).
"""

import struct
from array import array

# Au-delà, ce n'est plus un en-tête WAV plausible : on refuse plutôt que de
# bufferiser sans fin un flux qui n'est pas du WAV.
_TAILLE_MAX_ENTETE = 65536


def _entete_canonique(rate: int) -> bytes:
    """En-tête WAV PCM 16 bits mono de 44 octets. Les tailles RIFF/data sont
    inconnues en streaming : laissées à 0xFFFFFFFF (le helper Pipecat ne lit
    que le rate aux octets 24-28 et strippe l'en-tête sans les consulter)."""
    return (
        b"RIFF"
        + struct.pack("<I", 0xFFFFFFFF)
        + b"WAVE"
        + b"fmt "
        + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
        + b"data"
        + struct.pack("<I", 0xFFFFFFFF)
    )


def _float32_vers_pcm16(octets: bytes) -> bytes:
    """Convertit des échantillons float32 [-1, 1] en int16, avec écrêtage."""
    flottants = array("f")
    flottants.frombytes(octets)
    entiers = array("h", bytearray(2 * len(flottants)))
    for i, valeur in enumerate(flottants):
        if valeur > 1.0:
            valeur = 1.0
        elif valeur < -1.0:
            valeur = -1.0
        entiers[i] = int(valeur * 32767)
    return entiers.tobytes()


class NormaliseurWavPCM16:
    """Réécrit un flux WAV en WAV canonique PCM 16 bits, chunk par chunk."""

    def __init__(self) -> None:
        self._tampon = bytearray()
        self._entete_lue = False
        self._conversion_float32 = False
        self.rate: int | None = None

    def avaler(self, octets: bytes) -> bytes:
        """Absorbe un chunk du flux et rend les octets normalisés disponibles
        (vide tant que l'en-tête source n'est pas complètement parcourue)."""
        self._tampon.extend(octets)
        if not self._entete_lue:
            if not self._parcourir_entete():
                return b""
            # L'en-tête source vient d'être consommée : émettre la canonique
            # puis traiter ce qui reste déjà en tampon comme des données.
            return _entete_canonique(self.rate) + self._convertir_disponible()
        return self._convertir_disponible()

    def clore(self) -> bytes:
        """Fin du flux : abandonne un éventuel échantillon incomplet."""
        if not self._entete_lue or not self._conversion_float32:
            reste = bytes(self._tampon)
            self._tampon.clear()
            return reste
        # float32 : un reliquat < 4 octets est un échantillon tronqué, on le jette.
        self._tampon = self._tampon[: len(self._tampon) & ~3]
        return self._convertir_disponible()

    def _parcourir_entete(self) -> bool:
        """Marche les chunks RIFF jusqu'à `data`. Renvoie True quand l'en-tête
        est entièrement consommée (le tampon commence alors aux données)."""
        t = self._tampon
        if len(t) < 12:
            return False
        if t[0:4] != b"RIFF" or t[8:12] != b"WAVE":
            raise ValueError("flux inattendu : pas un WAV (magie RIFF/WAVE absente)")

        code_format = bits = None
        position = 12
        while True:
            if len(t) < position + 8:
                self._verifier_taille_entete()
                return False
            nom = bytes(t[position : position + 4])
            taille = struct.unpack("<I", t[position + 4 : position + 8])[0]
            if nom == b"fmt ":
                if len(t) < position + 8 + 16:
                    return False
                code_format, canaux, self.rate = struct.unpack(
                    "<HHI", t[position + 8 : position + 16]
                )
                bits = struct.unpack("<H", t[position + 22 : position + 24])[0]
                if canaux != 1:
                    raise ValueError(f"format WAV non géré : {canaux} canaux (mono attendu)")
            elif nom == b"data":
                if code_format is None:
                    raise ValueError("flux inattendu : chunk data avant fmt")
                if (code_format, bits) == (1, 16):
                    self._conversion_float32 = False
                elif (code_format, bits) == (3, 32):
                    self._conversion_float32 = True
                else:
                    raise ValueError(
                        f"format WAV non géré : code {code_format}, {bits} bits "
                        "(attendu : PCM 16 bits ou float 32 bits)"
                    )
                del t[: position + 8]
                self._entete_lue = True
                return True
            position += 8 + taille + (taille & 1)  # les chunks RIFF sont alignés pair
            self._verifier_taille_entete()

    def _verifier_taille_entete(self) -> None:
        if len(self._tampon) > _TAILLE_MAX_ENTETE:
            raise ValueError("en-tête WAV introuvable dans les 64 premiers Kio du flux")

    def _convertir_disponible(self) -> bytes:
        if not self._conversion_float32:
            reste = bytes(self._tampon)
            self._tampon.clear()
            return reste
        # Ne convertir que des float32 complets ; garder le reliquat pour après.
        aligne = len(self._tampon) & ~3
        if aligne == 0:
            return b""
        morceau = bytes(self._tampon[:aligne])
        del self._tampon[:aligne]
        return _float32_vers_pcm16(morceau)
