"""Adaptateur STT factice, scriptable par les tests. Aucun réseau."""

from dataclasses import dataclass, field

from app.stt.base import MoteurSTT


@dataclass
class STTFactice(MoteurSTT):
    """Moteur programmable. Chaque appel à `transcrire` consomme la prochaine
    réponse de `reponses` (dans l'ordre) ; une fois la liste épuisée, une
    valeur par défaut est renvoyée."""

    reponses: list[str] = field(default_factory=list)
    reponse_par_defaut: str = "Bonjour."
    # Journal des appels : les segments audio (copie) vus à chaque transcription.
    appels: list[bytes] = field(default_factory=list)

    async def transcrire(self, audio: bytes, *, langue: str = "fr") -> str:
        self.appels.append(audio)
        return self.reponses.pop(0) if self.reponses else self.reponse_par_defaut
