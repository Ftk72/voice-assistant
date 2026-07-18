"""Port du catalogue de voix (voice-forge vu par l'orchestrateur).

Sert le réglage grand public (ticket wayfinder 0014) : la liste **complète**
des voix enrôlées (pas seulement celles des personas), et l'aperçu audio de
chacune (bouton ▶).
"""

from abc import ABC, abstractmethod


class CatalogueVoix(ABC):
    @abstractmethod
    async def lister(self) -> list[dict]:
        """Toutes les voix enrôlées, chacune `{"id": str, "nom": str}`."""

    @abstractmethod
    async def apercu(self, voix_id: str) -> bytes:
        """Un extrait audio (WAV) de la voix `voix_id`."""
