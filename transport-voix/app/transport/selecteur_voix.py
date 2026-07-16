"""Choix de la voix TTS au fil du flux Dialogue Forge — logique pure.

Le Dialogue Forge annote chaque phrase de son flux `/tours` avec la voix
courante (ADR 0012 décision 5) ; le transport doit l'appliquer au TTS de ce
tour. Ce sélecteur, **sans aucune dépendance Pipecat**, décide *quand* un
changement de voix doit être signalé au service TTS : il part de la voix par
défaut sur laquelle le pipeline est monté (`s.tts_voix_defaut`) et ne renvoie
une voix que lorsqu'elle diffère de la voix appliquée jusqu'ici.

Isolé ici (plutôt que dans `dialogue_processor`, qui importe Pipecat) pour
rester testable sans l'extra `pipecat`.
"""


class SelecteurVoix:
    """Suit la voix appliquée au TTS et détecte les changements à signaler."""

    def __init__(self, voix_defaut: str) -> None:
        # Point de départ = voix sur laquelle le TTS a été construit.
        self._voix_courante = voix_defaut

    def changement(self, voix_phrase: str | None) -> str | None:
        """Renvoie la voix à appliquer au TTS avant de synthétiser cette phrase,
        ou `None` s'il n'y a rien à changer.

        `None` est renvoyé quand la phrase ne porte pas de voix (champ vide ou
        absent — la voix courante reste) ou quand sa voix est déjà la voix
        courante (pas de `TTSUpdateSettingsFrame` redondant au sein d'un tour)."""
        if not voix_phrase or voix_phrase == self._voix_courante:
            return None
        self._voix_courante = voix_phrase
        return voix_phrase
