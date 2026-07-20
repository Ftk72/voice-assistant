"""La fin d'une Tâche s'annonce comme l'échéance d'un minuteur (ADR 0008) —
sauf annulation, que l'utilisateur vient de demander et connaît déjà."""

from app.annonce.base import Annonceur
from app.annonce.journal import AnnonceurJournal
from app.atelier.fake import AtelierFactice
from app.boucle import BoucleCodeAct
from app.gestionnaire import GestionnaireTaches
from app.llm.factice import MoteurLLMFactice


class _AnnonceurQuiExplose(Annonceur):
    async def annoncer(self, texte: str) -> None:
        raise RuntimeError("le Pont hôte est injoignable")


def _gestionnaire(reponses: list[str], annonceur: Annonceur | None = None):
    llm = MoteurLLMFactice(reponses=reponses)
    boucle = BoucleCodeAct(moteur_llm=llm, budget_pas=8)
    atelier = AtelierFactice()
    annonceur = annonceur or AnnonceurJournal()
    gestionnaire = GestionnaireTaches(
        atelier_factory=lambda: atelier, boucle=boucle, annonceur=annonceur
    )
    return gestionnaire, annonceur


async def test_la_tache_terminee_est_annoncee():
    gestionnaire, annonceur = _gestionnaire(["TERMINÉ: fait."])

    tache = gestionnaire.confier("fais un truc")
    await gestionnaire.attendre_fin(tache.id)

    assert len(annonceur.dits) == 1
    assert "fait." in annonceur.dits[0]


async def test_la_tache_echouee_est_annoncee():
    llm_reponses = ["blabla non conforme"] * 8  # jamais de format valide : budget épuisé
    gestionnaire, annonceur = _gestionnaire(llm_reponses)

    tache = gestionnaire.confier("fais un truc")
    await gestionnaire.attendre_fin(tache.id)

    assert gestionnaire.obtenir(tache.id).statut == "echouee"
    assert len(annonceur.dits) == 1
    assert "n'ai pas réussi" in annonceur.dits[0]


async def test_la_tache_annulee_n_est_pas_annoncee():
    import asyncio

    from app.llm.base import MoteurLLM

    class _MoteurBloquant(MoteurLLM):
        async def completer(self, messages):
            await asyncio.Event().wait()

    boucle = BoucleCodeAct(moteur_llm=_MoteurBloquant(), budget_pas=8)
    atelier = AtelierFactice()
    annonceur = AnnonceurJournal()
    gestionnaire = GestionnaireTaches(
        atelier_factory=lambda: atelier, boucle=boucle, annonceur=annonceur
    )

    tache = gestionnaire.confier("fais un truc")
    await asyncio.sleep(0)
    await gestionnaire.annuler(tache.id)

    assert annonceur.dits == []


async def test_un_annonceur_qui_leve_n_empeche_pas_la_tache_de_finir():
    gestionnaire, _ = _gestionnaire(["TERMINÉ: fait."], annonceur=_AnnonceurQuiExplose())

    tache = gestionnaire.confier("fais un truc")
    await gestionnaire.attendre_fin(tache.id)

    assert gestionnaire.obtenir(tache.id).statut == "terminee"
    assert gestionnaire.obtenir(tache.id).compte_rendu == "fait."
