import pytest

from app.atelier.base import AtelierIndisponible
from app.atelier.fake import AtelierFactice
from app.schemas import ActionResultat


async def test_executer_avant_demarrage_leve_indisponible():
    atelier = AtelierFactice()

    with pytest.raises(AtelierIndisponible):
        await atelier.executer("echo bonjour")


async def test_demarrer_puis_executer_journalise_l_action_et_rend_le_resultat_prepare():
    resultat_prepare = ActionResultat(
        sortie_standard="bonjour\n", erreur_standard="", code_retour=0, duree_secondes=0.01
    )
    atelier = AtelierFactice(resultats=[resultat_prepare])

    await atelier.demarrer("tache-1")
    resultat = await atelier.executer("echo bonjour")

    assert resultat == resultat_prepare
    assert atelier.actions == ["echo bonjour"]
    assert atelier.tache_id == "tache-1"


async def test_executer_apres_destruction_leve_indisponible():
    atelier = AtelierFactice()
    await atelier.demarrer("tache-1")
    await atelier.detruire()

    with pytest.raises(AtelierIndisponible):
        await atelier.executer("echo bonjour")


async def test_sans_resultat_prepare_le_factice_rend_un_succes_vide():
    atelier = AtelierFactice()
    await atelier.demarrer("tache-1")

    resultat = await atelier.executer("true")

    assert resultat == ActionResultat(
        sortie_standard="", erreur_standard="", code_retour=0, duree_secondes=0.0
    )
