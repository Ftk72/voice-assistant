from typing import Literal

from pydantic import BaseModel

StatutTache = Literal["en_cours", "terminee", "echouee", "annulee"]


class ActionResultat(BaseModel):
    """Résultat d'une Action (un pas de la boucle CodeAct) exécutée dans l'Atelier."""

    sortie_standard: str
    erreur_standard: str
    code_retour: int
    duree_secondes: float


class TacheIn(BaseModel):
    """Énoncé en français libre d'une Tâche confiée à la forge."""

    enonce: str


class PasJournal(BaseModel):
    """Un pas de la boucle : l'Action jouée et son résultat dans l'Atelier."""

    code: str
    resultat: ActionResultat


class Tache(BaseModel):
    """Une Tâche confiée à l'action-forge (contrat 0031 : en mémoire au palier 1)."""

    id: str
    enonce: str
    statut: StatutTache = "en_cours"
    journal: list[PasJournal] = []
    compte_rendu: str | None = None
