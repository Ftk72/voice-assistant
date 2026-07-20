import asyncio

import pytest

from app.annonce.journal import AnnonceurJournal
from app.atelier.fake import AtelierFactice
from app.boucle import BoucleCodeAct
from app.gestionnaire import GestionnaireTaches
from app.llm.base import MoteurLLM
from app.llm.factice import MoteurLLMFactice
from app.schemas import ActionResultat


class _MoteurBloquant(MoteurLLM):
    """Ne répond jamais seul — pour tester l'annulation d'une Tâche en cours."""

    async def completer(self, messages):
        await asyncio.Event().wait()


def _gestionnaire(reponses: list[str], resultats: list[ActionResultat] | None = None):
    llm = MoteurLLMFactice(reponses=reponses)
    boucle = BoucleCodeAct(moteur_llm=llm, budget_pas=8)
    atelier = AtelierFactice(resultats=resultats)
    gestionnaire = GestionnaireTaches(
        atelier_factory=lambda: atelier, boucle=boucle, annonceur=AnnonceurJournal()
    )
    return gestionnaire, atelier


async def test_confier_cree_une_tache_en_cours_puis_la_termine():
    gestionnaire, _ = _gestionnaire(["TERMINÉ: fait."])

    tache = gestionnaire.confier("fais un truc")
    assert tache.statut == "en_cours"

    await gestionnaire.attendre_fin(tache.id)

    assert gestionnaire.obtenir(tache.id).statut == "terminee"
    assert gestionnaire.obtenir(tache.id).compte_rendu == "fait."


async def test_obtenir_tache_inconnue_rend_none():
    gestionnaire, _ = _gestionnaire([])

    assert gestionnaire.obtenir("inconnue") is None


async def test_lister_rend_toutes_les_taches_confiees():
    gestionnaire, _ = _gestionnaire(["TERMINÉ: un.", "TERMINÉ: deux."])

    t1 = gestionnaire.confier("premiere")
    await gestionnaire.attendre_fin(t1.id)
    t2 = gestionnaire.confier("deuxieme")
    await gestionnaire.attendre_fin(t2.id)

    ids = {t.id for t in gestionnaire.lister()}
    assert ids == {t1.id, t2.id}


async def test_atelier_demarre_avec_l_id_de_la_tache_puis_detruit_a_la_fin():
    gestionnaire, atelier = _gestionnaire(["TERMINÉ: fait."])

    tache = gestionnaire.confier("fais un truc")
    await gestionnaire.attendre_fin(tache.id)

    assert atelier.tache_id == tache.id
    assert atelier.detruit


async def test_annuler_une_tache_en_cours_la_marque_annulee_et_detruit_l_atelier():
    boucle = BoucleCodeAct(moteur_llm=_MoteurBloquant(), budget_pas=8)
    atelier = AtelierFactice()
    gestionnaire = GestionnaireTaches(
        atelier_factory=lambda: atelier, boucle=boucle, annonceur=AnnonceurJournal()
    )

    tache = gestionnaire.confier("fais un truc")
    await asyncio.sleep(0)  # laisse la boucle atteindre l'attente bloquante du LLM
    assert tache.statut == "en_cours"

    annulee = await gestionnaire.annuler(tache.id)

    assert annulee is True
    assert gestionnaire.obtenir(tache.id).statut == "annulee"
    assert atelier.detruit


async def test_annuler_une_tache_deja_terminee_rend_faux():
    gestionnaire, _ = _gestionnaire(["TERMINÉ: fait."])

    tache = gestionnaire.confier("fais un truc")
    await gestionnaire.attendre_fin(tache.id)

    assert await gestionnaire.annuler(tache.id) is False


async def test_annuler_une_tache_inconnue_rend_faux():
    gestionnaire, _ = _gestionnaire([])

    assert await gestionnaire.annuler("inconnue") is False


async def test_flux_publie_les_evenements_puis_se_ferme():
    resultat = ActionResultat(
        sortie_standard="ok\n", erreur_standard="", code_retour=0, duree_secondes=0.01
    )
    gestionnaire, _ = _gestionnaire(
        ["```bash\necho ok\n```", "TERMINÉ: fait."], resultats=[resultat]
    )

    tache = gestionnaire.confier("fais un truc")
    evenements = [e async for e in gestionnaire.flux(tache.id)]

    types = [e["type"] for e in evenements]
    assert types == ["action", "terminee"]


async def test_flux_d_une_tache_inconnue_rend_none():
    gestionnaire, _ = _gestionnaire([])

    with pytest.raises(KeyError):
        [_ async for _ in gestionnaire.flux("inconnue")]
