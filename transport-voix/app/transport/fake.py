"""Adaptateur transport factice. Aucun réseau, aucun matériel."""

from dataclasses import dataclass

from app.transport.base import Transport


@dataclass
class TransportFactice(Transport):
    """Bascule un simple booléen `actif`, pour les assertions de tests."""

    actif: bool = False

    async def demarrer(self) -> None:
        self.actif = True

    async def arreter(self) -> None:
        self.actif = False
