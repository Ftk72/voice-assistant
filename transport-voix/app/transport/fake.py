"""Adaptateur transport factice. Aucun réseau, aucun matériel."""

from dataclasses import dataclass, field

from app.transport.base import Transport


@dataclass
class TransportFactice(Transport):
    """Bascule un simple booléen `actif`, pour les assertions de tests.

    `ouverte` simule l'état d'une conversation temps réel (programmable par les
    tests) et `annonces_jouees` journalise les WAV qu'on lui a confiés — de quoi
    exercer l'arbitrage du Pont hôte sans aucune session WebRTC (ticket 0044)."""

    actif: bool = False
    ouverte: bool = False
    annonces_jouees: list[bytes] = field(default_factory=list)

    async def demarrer(self) -> None:
        self.actif = True

    async def arreter(self) -> None:
        self.actif = False

    def conversation_ouverte(self) -> bool:
        return self.ouverte

    async def jouer_annonce(self, wav: bytes) -> bool:
        if not self.ouverte:
            return False
        self.annonces_jouees.append(wav)
        return True
