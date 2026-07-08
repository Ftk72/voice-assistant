"""Adaptateur transport réel (Pipecat/WebRTC).

⚠️ Prémisses différées (ADR 0012) — À LIRE AVANT TOUTE MODIFICATION :
le pont WebRTC WebView2↔Pipecat n'a **jamais été prototypé**, et les imports
exacts de Pipecat 1.5 (p. ex. `SmallWebRTCTransport`, le protocole RTVI) ne
sont **pas vérifiés**. Cette classe n'invente donc aucune API Pipecat et ne
fait aucun `import pipecat` au niveau module : c'est un stub honnête qui lève
`NotImplementedError`, en attendant un prototypage réel."""

from app.config import Settings
from app.transport.base import Transport


class TransportPipecat(Transport):
    """Adaptateur réel, jamais exécuté à ce jour — cf. docstring du module."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def demarrer(self) -> None:
        raise NotImplementedError(
            "Pont WebRTC WebView2↔Pipecat non encore prototypé — cf. ADR 0012, "
            "prémisses différées"
        )

    async def arreter(self) -> None:
        raise NotImplementedError(
            "Pont WebRTC WebView2↔Pipecat non encore prototypé — cf. ADR 0012, "
            "prémisses différées"
        )
