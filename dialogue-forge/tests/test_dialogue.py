import json

from fastapi.testclient import TestClient

from app.config import Settings
from app.dialogue import CONSIGNES_OUTILS
from app.llm.base import AppelOutil
from app.llm.fake import TourOutils, TourTexte
from app.main import create_app


def _lignes(reponse) -> list[dict]:
    return [json.loads(ligne) for ligne in reponse.text.splitlines() if ligne.strip()]


def _nouvelle_conversation(client, persona="assistant") -> str:
    return client.post("/conversations", json={"persona": persona}).json()["id"]


def test_un_tour_simple_est_streame_phrase_par_phrase(client):
    client.app.state.llm.tours = [TourTexte("Bonjour toi. Comment vas-tu ?")]
    identifiant = _nouvelle_conversation(client)

    reponse = client.post(f"/conversations/{identifiant}/tours", json={"texte": "Salut"})
    assert reponse.status_code == 200
    lignes = _lignes(reponse)

    phrases = [ligne["texte"] for ligne in lignes if ligne["type"] == "phrase"]
    assert phrases == ["Bonjour toi.", "Comment vas-tu ?"]

    fin = lignes[-1]
    assert fin["type"] == "fin"
    assert fin["reponse"] == "Bonjour toi. Comment vas-tu ?"


def test_l_injection_place_les_faits_dans_un_message_utilisateur_de_contexte(client):
    client.app.state.memoire.faits = ["Le chat de l'utilisateur s'appelle Félix."]
    client.app.state.llm.tours = [TourTexte("Bien noté.")]
    identifiant = _nouvelle_conversation(client)

    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Tu te souviens du chat ?"})

    messages = client.app.state.llm.appels_generation[0]
    systeme = next(m for m in messages if m["role"] == "system")
    assert "Félix" not in systeme["content"]

    messages_contexte = [
        m
        for m in messages
        if m["role"] == "user" and "[Contexte mémoire" in (m["content"] or "")
    ]
    assert len(messages_contexte) == 1
    assert "Félix" in messages_contexte[0]["content"]

    # Le message de contexte précède bien le message utilisateur du tour.
    index_contexte = messages.index(messages_contexte[0])
    index_utilisateur = next(
        i
        for i, m in enumerate(messages)
        if m["role"] == "user" and m["content"] == "Tu te souviens du chat ?"
    )
    assert index_contexte < index_utilisateur


def test_le_systeme_contient_le_prompt_persona_et_le_bloc_de_consignes_outils(client):
    client.app.state.llm.tours = [TourTexte("D'accord.")]
    identifiant = _nouvelle_conversation(client, persona="assistant")

    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Salut"})

    systeme = next(m for m in client.app.state.llm.appels_generation[0] if m["role"] == "system")
    persona = client.app.state.personas["assistant"]

    assert systeme["content"].startswith(persona.prompt)
    assert systeme["content"] == f"{persona.prompt}\n\n{CONSIGNES_OUTILS}"
    assert "recall" in systeme["content"]


def test_le_bloc_de_consignes_outils_est_identique_entre_deux_personas(client):
    client.app.state.llm.tours = [TourTexte("D'accord."), TourTexte("Grrr.")]
    id_assistant = _nouvelle_conversation(client, persona="assistant")
    id_batman = _nouvelle_conversation(client, persona="batman")

    client.post(f"/conversations/{id_assistant}/tours", json={"texte": "Salut"})
    client.post(f"/conversations/{id_batman}/tours", json={"texte": "Salut"})

    systeme_assistant = next(
        m for m in client.app.state.llm.appels_generation[0] if m["role"] == "system"
    )
    systeme_batman = next(
        m for m in client.app.state.llm.appels_generation[1] if m["role"] == "system"
    )
    assert systeme_assistant["content"].endswith(CONSIGNES_OUTILS)
    assert systeme_batman["content"].endswith(CONSIGNES_OUTILS)


def test_le_message_systeme_est_identique_octet_pour_octet_entre_deux_tours(client):
    client.app.state.memoire.faits = ["Le chat de l'utilisateur s'appelle Félix."]
    client.app.state.llm.tours = [TourTexte("Bien noté."), TourTexte("Toujours d'accord.")]
    identifiant = _nouvelle_conversation(client)

    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Premier tour"})
    # Le second tour ne renvoie plus aucun fait : le système ne doit pas bouger.
    client.app.state.memoire.faits = []
    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Second tour"})

    premier_systeme = next(
        m for m in client.app.state.llm.appels_generation[0] if m["role"] == "system"
    )
    second_systeme = next(
        m for m in client.app.state.llm.appels_generation[1] if m["role"] == "system"
    )
    assert premier_systeme == second_systeme


def test_le_message_contexte_est_persiste_dans_l_historique(client):
    client.app.state.memoire.faits = ["Le chat de l'utilisateur s'appelle Félix."]
    client.app.state.llm.tours = [TourTexte("Bien noté."), TourTexte("Toujours d'accord.")]
    identifiant = _nouvelle_conversation(client)

    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Premier tour"})

    historique_api = client.get(f"/conversations/{identifiant}").json()["historique"]
    contextes = [
        m
        for m in historique_api
        if m["role"] == "user" and "[Contexte mémoire" in (m["content"] or "")
    ]
    assert len(contextes) == 1

    # Visible aussi au tour suivant, dans les messages envoyés au LLM.
    client.app.state.memoire.faits = []
    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Deuxième tour"})
    second_messages = client.app.state.llm.appels_generation[1]
    assert any(
        m["role"] == "user" and "Félix" in (m["content"] or "") for m in second_messages
    )


def test_aucun_message_contexte_quand_la_memoire_ne_renvoie_rien(client):
    client.app.state.memoire.faits = []
    client.app.state.llm.tours = [TourTexte("D'accord.")]
    identifiant = _nouvelle_conversation(client)

    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Salut"})

    messages = client.app.state.llm.appels_generation[0]
    assert not any("[Contexte mémoire" in (m["content"] or "") for m in messages)

    historique_api = client.get(f"/conversations/{identifiant}").json()["historique"]
    assert not any("[Contexte mémoire" in (m["content"] or "") for m in historique_api)


def test_lister_outils_n_est_appele_qu_une_fois_pour_deux_tours(client):
    # L'appel a déjà eu lieu une fois pendant le lifespan (démarrage de l'app).
    assert client.app.state.outils.appels_lister_outils == 1

    client.app.state.llm.tours = [TourTexte("Un."), TourTexte("Deux.")]
    identifiant = _nouvelle_conversation(client)

    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Un"})
    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Deux"})

    assert client.app.state.outils.appels_lister_outils == 1


def test_l_episode_est_capture_apres_le_tour(client):
    client.app.state.llm.tours = [TourTexte("Avec plaisir.")]
    identifiant = _nouvelle_conversation(client, persona="batman")

    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Bonsoir"})

    episodes = client.app.state.memoire.episodes
    assert len(episodes) == 1
    assert episodes[0].nom == "Batman"
    assert "Bonsoir" in episodes[0].contenu
    assert "Avec plaisir." in episodes[0].contenu


def test_la_boucle_d_outils_renvoie_le_resultat_au_llm(client):
    client.app.state.outils.definitions = [
        {"type": "function", "function": {"name": "meteo", "description": "Météo"}}
    ]
    client.app.state.outils.resultats = {"meteo": "vingt-trois degrés et ensoleillé"}
    client.app.state.llm.tours = [
        TourOutils([AppelOutil(id="a1", nom="meteo", arguments='{"ville": "Paris"}')]),
        TourTexte("Il fait vingt-trois degrés."),
    ]
    identifiant = _nouvelle_conversation(client)

    reponse = client.post(
        f"/conversations/{identifiant}/tours", json={"texte": "Quel temps fait-il ?"}
    )
    lignes = _lignes(reponse)

    assert client.app.state.outils.appels == [("meteo", {"ville": "Paris"})]
    assert lignes[-1]["reponse"] == "Il fait vingt-trois degrés."

    # Le second appel LLM a bien reçu le résultat de l'outil.
    seconds_messages = client.app.state.llm.appels_generation[1]
    assert any(
        m["role"] == "tool" and "vingt-trois" in m["content"] for m in seconds_messages
    )


def test_les_messages_de_la_boucle_d_outils_sont_persistes_dans_l_historique(client):
    client.app.state.outils.definitions = [
        {"type": "function", "function": {"name": "meteo", "description": "Météo"}}
    ]
    client.app.state.outils.resultats = {"meteo": "vingt-trois degrés et ensoleillé"}
    client.app.state.llm.tours = [
        TourOutils([AppelOutil(id="a1", nom="meteo", arguments='{"ville": "Paris"}')]),
        TourTexte("Il fait vingt-trois degrés."),
    ]
    identifiant = _nouvelle_conversation(client)

    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Quel temps fait-il ?"})

    historique_api = client.get(f"/conversations/{identifiant}").json()["historique"]
    roles = [m["role"] for m in historique_api]
    assert roles == ["user", "assistant", "tool", "assistant"]

    message_utilisateur, message_assistant_outil, message_outil, message_final = historique_api
    assert message_utilisateur["content"] == "Quel temps fait-il ?"
    assert message_assistant_outil["tool_calls"][0]["function"]["name"] == "meteo"
    assert message_outil["tool_call_id"] == "a1"
    assert "vingt-trois" in message_outil["content"]
    assert message_final["content"] == "Il fait vingt-trois degrés."


def test_le_tour_suivant_apres_outil_renvoie_un_prefixe_identique_au_dernier_appel(client):
    client.app.state.outils.definitions = [
        {"type": "function", "function": {"name": "meteo", "description": "Météo"}}
    ]
    client.app.state.outils.resultats = {"meteo": "vingt-trois degrés et ensoleillé"}
    client.app.state.llm.tours = [
        TourOutils([AppelOutil(id="a1", nom="meteo", arguments='{"ville": "Paris"}')]),
        TourTexte("Il fait vingt-trois degrés."),
        TourTexte("Un mot : chaud."),
    ]
    identifiant = _nouvelle_conversation(client)

    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Quel temps fait-il ?"})
    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Redis-moi ça en un mot"})

    dernier_appel_premier_tour = client.app.state.llm.appels_generation[1]
    premier_appel_second_tour = client.app.state.llm.appels_generation[2]

    prefixe = premier_appel_second_tour[: len(dernier_appel_premier_tour)]
    assert prefixe == dernier_appel_premier_tour


def test_la_limite_d_iterations_d_outils_arrete_la_boucle(personas_dir):
    settings = Settings(personas_dir=personas_dir, max_iterations_outils=2)
    app = create_app(settings)
    with TestClient(app) as client:
        # Le LLM factice demande un outil à *chaque* tour (boucle qui n'aboutit pas).
        app.state.llm.tour_par_defaut = TourOutils(
            [AppelOutil(id="x", nom="tourne", arguments="{}")]
        )
        app.state.outils.resultats = {"tourne": "encore"}
        identifiant = client.post("/conversations", json={"persona": "assistant"}).json()["id"]

        reponse = client.post(
            f"/conversations/{identifiant}/tours", json={"texte": "Boucle"}
        )
        lignes = _lignes(reponse)

        # On s'arrête après exactement max_iterations_outils exécutions d'outils.
        assert len(app.state.outils.appels) == 2
        assert lignes[-1]["type"] == "fin"


def test_l_historique_multitours_est_vu_au_second_tour(client):
    client.app.state.llm.tours = [TourTexte("Premier."), TourTexte("Second.")]
    identifiant = _nouvelle_conversation(client)

    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Un"})
    client.post(f"/conversations/{identifiant}/tours", json={"texte": "Deux"})

    seconds_messages = client.app.state.llm.appels_generation[1]
    contenus = [m.get("content") for m in seconds_messages]
    assert "Un" in contenus
    assert "Premier." in contenus

    historique = client.get(f"/conversations/{identifiant}").json()["historique"]
    assert [m["content"] for m in historique] == ["Un", "Premier.", "Deux", "Second."]
