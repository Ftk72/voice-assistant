from app.atelier.base import AtelierIndisponible
from app.atelier.fake import AtelierFactice
from app.boucle import BoucleCodeAct
from app.llm.factice import MoteurLLMFactice
from app.schemas import ActionResultat, Tache


def _tache(enonce: str = "dis bonjour") -> Tache:
    return Tache(id="tache-1", enonce=enonce)


async def test_compte_rendu_immediat_sans_action():
    llm = MoteurLLMFactice(reponses=["TERMINÉ: rien à faire, tout était déjà en ordre."])
    atelier = AtelierFactice()
    await atelier.demarrer("tache-1")
    boucle = BoucleCodeAct(moteur_llm=llm, budget_pas=8)
    tache = _tache()

    await boucle.executer(tache, atelier)

    assert tache.statut == "terminee"
    assert tache.compte_rendu == "rien à faire, tout était déjà en ordre."
    assert tache.journal == []


async def test_une_action_puis_compte_rendu():
    resultat = ActionResultat(
        sortie_standard="bonjour\n", erreur_standard="", code_retour=0, duree_secondes=0.01
    )
    llm = MoteurLLMFactice(
        reponses=["```bash\necho bonjour\n```", "TERMINÉ: le fichier a été créé."]
    )
    atelier = AtelierFactice(resultats=[resultat])
    await atelier.demarrer("tache-1")
    boucle = BoucleCodeAct(moteur_llm=llm, budget_pas=8)
    tache = _tache()

    await boucle.executer(tache, atelier)

    assert tache.statut == "terminee"
    assert tache.compte_rendu == "le fichier a été créé."
    assert len(tache.journal) == 1
    assert tache.journal[0].code == "echo bonjour"
    assert tache.journal[0].resultat == resultat
    # L'observation (stdout) doit avoir été réinjectée au tour suivant.
    assert "bonjour" in llm.messages_recus[1][-1]["content"]


async def test_budget_de_pas_epuise_echoue_proprement():
    llm = MoteurLLMFactice(reponses=["```bash\necho encore\n```"] * 3)
    atelier = AtelierFactice()
    await atelier.demarrer("tache-1")
    boucle = BoucleCodeAct(moteur_llm=llm, budget_pas=3)
    tache = _tache()

    await boucle.executer(tache, atelier)

    assert tache.statut == "echouee"
    assert "budget" in tache.compte_rendu.lower()
    assert len(tache.journal) == 3


async def test_atelier_indisponible_echoue_proprement_sans_boucler():
    class AtelierCasse(AtelierFactice):
        async def executer(self, code: str) -> ActionResultat:
            raise AtelierIndisponible("Docker injoignable")

    llm = MoteurLLMFactice(reponses=["```bash\necho x\n```", "TERMINÉ: ne devrait jamais arriver"])
    atelier = AtelierCasse()
    await atelier.demarrer("tache-1")
    boucle = BoucleCodeAct(moteur_llm=llm, budget_pas=8)
    tache = _tache()

    await boucle.executer(tache, atelier)

    assert tache.statut == "echouee"
    assert "Docker injoignable" in tache.compte_rendu
    assert llm.messages_recus == [llm.messages_recus[0]]  # un seul appel LLM


async def test_reponse_mal_formee_compte_comme_un_pas_et_redemande_le_format():
    llm = MoteurLLMFactice(
        reponses=["je ne sais pas trop quoi faire", "TERMINÉ: c'était juste un faux départ."]
    )
    atelier = AtelierFactice()
    await atelier.demarrer("tache-1")
    boucle = BoucleCodeAct(moteur_llm=llm, budget_pas=8)
    tache = _tache()

    await boucle.executer(tache, atelier)

    assert tache.statut == "terminee"
    assert tache.compte_rendu == "c'était juste un faux départ."
    assert tache.journal == []


async def test_evenements_notifies_a_chaque_pas():
    resultat = ActionResultat(
        sortie_standard="ok\n", erreur_standard="", code_retour=0, duree_secondes=0.01
    )
    llm = MoteurLLMFactice(reponses=["```bash\necho ok\n```", "TERMINÉ: fini."])
    atelier = AtelierFactice(resultats=[resultat])
    await atelier.demarrer("tache-1")
    boucle = BoucleCodeAct(moteur_llm=llm, budget_pas=8)
    tache = _tache()
    evenements = []

    await boucle.executer(tache, atelier, sur_evenement=evenements.append)

    types = [e["type"] for e in evenements]
    assert types == ["action", "terminee"]
