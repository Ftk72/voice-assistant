"""Adaptateur TTS factice, scriptable par les tests. Aucun réseau."""

from dataclasses import dataclass, field

from app.tts.base import MoteurTTS


@dataclass
class TTSFactice(MoteurTTS):
    """Moteur programmable : renvoie des octets déterministes (encodage du
    texte) et journalise les appels reçus, pour les assertions de tests."""

    appels: list[tuple[str, str]] = field(default_factory=list)

    async def synthetiser(self, texte: str, *, voix: str) -> bytes:
        self.appels.append((texte, voix))
        return texte.encode()
