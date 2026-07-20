from abc import ABC, abstractmethod

from app.schemas import ActionResultat


class AtelierIndisponible(Exception):
    """L'Atelier n'a pas pu démarrer ou exécuter l'Action demandée (image absente,
    Docker injoignable, ou Atelier détruit/jamais démarré)."""


class Atelier(ABC):
    """Port du bac à sable jetable (ADR 0013, contrat du ticket 0031) : un Atelier
    par Tâche, borné en CPU/RAM/temps, détruit après le Compte rendu. Il ne voit
    jamais le dépôt, les secrets ni le socket Docker ; son seul montage est le
    sous-dossier d'échange de sa Tâche."""

    @abstractmethod
    async def demarrer(self, tache_id: str) -> None:
        """Crée le conteneur jetable de la Tâche `tache_id`, sans réseau par défaut."""

    @abstractmethod
    async def executer(self, code: str) -> ActionResultat:
        """Exécute une Action (du code, paradigme CodeAct) dans l'Atelier démarré et
        renvoie son résultat. `AtelierIndisponible` si l'Atelier n'est pas démarré."""

    @abstractmethod
    async def detruire(self) -> None:
        """Détruit le conteneur — appelé après le Compte rendu, échec compris."""
