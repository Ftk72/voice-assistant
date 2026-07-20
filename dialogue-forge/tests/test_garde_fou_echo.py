"""Ticket 0044 (garde-fou) : un tour utilisateur qui n'est que l'écho, capté
par le micro, de la réponse assistant qui le précède immédiatement ne doit
jamais devenir un souvenir. C'est un filet de sécurité *local* à
`clore_conversation` — le correctif structurel (canal des annonces) est
traité ailleurs (cf. ticket 0044) ; ces tests ne couvrent que ce garde-fou.

Construction directe d'un `Orchestrateur` avec les adaptateurs factices, à
l'image de `tests/test_tolerance_forges_outils.py` : pas de HTTP, un
historique bâti à la main pour contrôler précisément l'enchaînement des
tours assistant/utilisateur.
"""

from app.dialogue import Orchestrateur
from app.llm.fake import MoteurLLMFactice
from app.memoire.fake import MemoireFactice
from app.outils.fake import OutilsFactices


def _orchestrateur() -> tuple[Orchestrateur, MemoireFactice]:
    memoire = MemoireFactice()
    orchestrateur = Orchestrateur(MoteurLLMFactice(), memoire, OutilsFactices())
    return orchestrateur, memoire


async def test_un_echo_mot_pour_mot_n_est_pas_memorise():
    orchestrateur, memoire = _orchestrateur()
    historique = [
        {"role": "assistant", "content": "La tâche est terminée avec succès."},
        {"role": "user", "content": "La tâche est terminée avec succès."},
    ]
    capture = await orchestrateur.clore_conversation(historique, nom="conv")
    assert capture is False
    assert memoire.episodes == []


async def test_un_echo_tel_que_rendu_par_le_stt_n_est_pas_memorise():
    # Casse perdue, ponctuation absente, une élision différente : ce qu'un
    # STT restitue réellement, pas un copier-coller exact.
    orchestrateur, memoire = _orchestrateur()
    historique = [
        {"role": "assistant", "content": "La tâche est terminée avec succès."},
        {"role": "user", "content": "la tache est terminee avec succes"},
    ]
    capture = await orchestrateur.clore_conversation(historique, nom="conv")
    assert capture is False
    assert memoire.episodes == []


async def test_un_tour_utilisateur_sans_rapport_est_memorise():
    # Non-régression : le cas nominal ne doit pas se dégrader.
    orchestrateur, memoire = _orchestrateur()
    historique = [
        {"role": "assistant", "content": "La tâche est terminée avec succès."},
        {"role": "user", "content": "J'ai un chien qui s'appelle Rex."},
    ]
    capture = await orchestrateur.clore_conversation(historique, nom="conv")
    assert capture is True
    assert len(memoire.episodes) == 1
    assert "Rex" in memoire.episodes[0].contenu


async def test_un_backchannel_court_reste_ecarte_sans_regression():
    # « bien », seul, est un backchannel (BACKCHANNELS) — pas un écho, mais
    # écarté par le filtre existant, qui doit continuer d'agir sans que le
    # nouveau garde-fou ne le perturbe.
    orchestrateur, memoire = _orchestrateur()
    historique = [
        {"role": "assistant", "content": "Je m'y mets tout de suite."},
        {"role": "user", "content": "bien"},
    ]
    capture = await orchestrateur.clore_conversation(historique, nom="conv")
    assert capture is False
    assert memoire.episodes == []


async def test_une_reformulation_reprenant_quelques_mots_est_memorisee():
    # Protection contre le faux positif : réutiliser deux ou trois mots de
    # l'assistant dans une reformulation n'est pas un écho.
    orchestrateur, memoire = _orchestrateur()
    historique = [
        {
            "role": "assistant",
            "content": "La tâche de déploiement est terminée avec succès.",
        },
        {"role": "user", "content": "La tâche a pris combien de temps au juste ?"},
    ]
    capture = await orchestrateur.clore_conversation(historique, nom="conv")
    assert capture is True
    assert len(memoire.episodes) == 1


async def test_un_premier_tour_utilisateur_sans_assistant_avant_est_memorise():
    # Aucun tour assistant avant lui dans l'historique : ne doit jamais lever
    # d'IndexError, et doit être mémorisé normalement.
    orchestrateur, memoire = _orchestrateur()
    historique = [{"role": "user", "content": "Bonjour, je m'appelle Camille."}]
    capture = await orchestrateur.clore_conversation(historique, nom="conv")
    assert capture is True
    assert len(memoire.episodes) == 1


async def test_une_conversation_entierement_faite_d_echos_ne_capture_rien():
    orchestrateur, memoire = _orchestrateur()
    historique = [
        {"role": "assistant", "content": "Le minuteur vient de sonner."},
        {"role": "user", "content": "le minuteur vient de sonner"},
        {"role": "assistant", "content": "La tâche est terminée."},
        {"role": "user", "content": "la tache est terminee"},
    ]
    capture = await orchestrateur.clore_conversation(historique, nom="conv")
    assert capture is False
    assert memoire.episodes == []
