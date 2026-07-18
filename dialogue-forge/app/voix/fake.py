"""Adaptateur catalogue de voix factice. Aucun réseau."""

from dataclasses import dataclass, field

from app.voix.base import CatalogueVoix

# Entête RIFF/WAVE minimal (pas de données) : suffit à faire un WAV valide
# pour les tests d'aperçu.
_WAV_MINIMAL = (
    b"RIFF" + (36).to_bytes(4, "little") + b"WAVE"
    b"fmt " + (16).to_bytes(4, "little")
    + (1).to_bytes(2, "little")  # PCM
    + (1).to_bytes(2, "little")  # mono
    + (16000).to_bytes(4, "little")  # fréquence d'échantillonnage
    + (32000).to_bytes(4, "little")  # octets/s
    + (2).to_bytes(2, "little")  # alignement bloc
    + (16).to_bytes(2, "little")  # bits/échantillon
    + b"data" + (0).to_bytes(4, "little")
)


@dataclass
class CatalogueVoixFactice(CatalogueVoix):
    """Catalogue programmable : `voix` est renvoyé tel quel par `lister` ; si
    `echoue` vaut vrai, `lister` lève (pour tester le repli sur les voix des
    personas). `apercu` renvoie toujours un WAV minimal valide."""

    voix: list[dict] = field(
        default_factory=lambda: [
            {"id": "VoixDeTest", "nom": "VoixDeTest"},
            {"id": "Emma", "nom": "Emma"},
        ]
    )
    echoue: bool = False

    async def lister(self) -> list[dict]:
        if self.echoue:
            raise RuntimeError("Catalogue de voix indisponible (factice, echoue=True)")
        return list(self.voix)

    async def apercu(self, voix_id: str) -> bytes:
        return _WAV_MINIMAL
