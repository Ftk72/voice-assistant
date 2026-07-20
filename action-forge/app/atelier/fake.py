from app.atelier.base import Atelier, AtelierIndisponible
from app.schemas import ActionResultat


class AtelierFactice(Atelier):
    """Zéro Docker, zéro réseau : journalise les Actions reçues et renvoie des
    résultats préparés (pattern ExecuteurCypherFactice de memory-forge) — utilisé
    par les tests."""

    def __init__(self, resultats: list[ActionResultat] | None = None) -> None:
        self._resultats = list(resultats or [])
        self.tache_id: str | None = None
        self.demarre = False
        self.detruit = False
        self.actions: list[str] = []

    async def demarrer(self, tache_id: str) -> None:
        self.tache_id = tache_id
        self.demarre = True
        self.detruit = False

    async def executer(self, code: str) -> ActionResultat:
        if not self.demarre or self.detruit:
            raise AtelierIndisponible("l'Atelier n'est pas démarré")
        self.actions.append(code)
        if self._resultats:
            return self._resultats.pop(0)
        return ActionResultat(
            sortie_standard="", erreur_standard="", code_retour=0, duree_secondes=0.0
        )

    async def detruire(self) -> None:
        self.demarre = False
        self.detruit = True
