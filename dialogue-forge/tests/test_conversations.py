from fastapi.testclient import TestClient

from app.config import Settings
from app.llm.fake import TourTexte
from app.main import create_app


def _jouer(client, cid, texte):
    return client.post(f"/conversations/{cid}/tours", json={"texte": texte})


def test_creation_de_conversation_avec_persona(client):
    reponse = client.post("/conversations", json={"persona": "batman"})
    assert reponse.status_code == 201
    identifiant = reponse.json()["id"]

    vue = client.get(f"/conversations/{identifiant}")
    assert vue.status_code == 200
    assert vue.json()["persona"] == "Batman"
    assert vue.json()["historique"] == []


def test_creation_avec_persona_par_defaut(client):
    reponse = client.post("/conversations", json={})
    assert reponse.status_code == 201
    identifiant = reponse.json()["id"]
    assert client.get(f"/conversations/{identifiant}").json()["persona"] == "Assistant"


def test_persona_inconnu_refuse(client):
    assert client.post("/conversations", json={"persona": "joker"}).status_code == 404


def test_conversation_inconnue_404(client):
    assert client.get("/conversations/inexistante").status_code == 404
    tour = client.post("/conversations/inexistante/tours", json={"texte": "Salut"})
    assert tour.status_code == 404


# --- Capture par conversation (ADR 0011) -----------------------------------


def test_rien_n_est_capture_avant_la_cloture(client):
    # La capture n'a plus lieu par tour : elle attend la fermeture (ADR 0011).
    client.app.state.llm.tours = [TourTexte("Bien.")]
    cid = client.post("/conversations", json={"persona": "batman"}).json()["id"]
    _jouer(client, cid, "J'ai un chien.")
    assert client.app.state.memoire.episodes == []


def test_la_cloture_capture_un_episode_unique(client):
    client.app.state.llm.tours = [TourTexte("Bien."), TourTexte("Noté.")]
    cid = client.post("/conversations", json={"persona": "batman"}).json()["id"]
    _jouer(client, cid, "J'ai un chien.")
    _jouer(client, cid, "Il s'appelle Rex.")
    reponse = client.post(f"/conversations/{cid}/clore")
    assert reponse.status_code == 200
    assert reponse.json()["episode_capture"] is True
    assert len(client.app.state.memoire.episodes) == 1


def test_l_episode_ne_contient_que_l_utilisateur(client):
    # L'assistant ne fait pas foi : sa réponse ne doit jamais entrer en mémoire.
    client.app.state.llm.tours = [TourTexte("Phrase de l'assistant a ne pas memoriser.")]
    cid = client.post("/conversations", json={"persona": "batman"}).json()["id"]
    _jouer(client, cid, "Je suis allergique aux noix.")
    client.post(f"/conversations/{cid}/clore")
    contenu = client.app.state.memoire.episodes[0].contenu
    assert "noix" in contenu
    assert "a ne pas memoriser" not in contenu


def test_les_backchannels_sont_exclus_de_l_episode(client):
    client.app.state.llm.tours = [TourTexte("A."), TourTexte("B."), TourTexte("C.")]
    cid = client.post("/conversations", json={"persona": "batman"}).json()["id"]
    _jouer(client, cid, "J'habite a Lyon.")
    _jouer(client, cid, "Oui.")
    _jouer(client, cid, "Merci.")
    client.post(f"/conversations/{cid}/clore")
    contenu = client.app.state.memoire.episodes[0].contenu
    assert "Lyon" in contenu
    assert "Oui" not in contenu
    assert "Merci" not in contenu


def test_une_conversation_sans_contenu_utile_ne_capture_rien(client):
    client.app.state.llm.tours = [TourTexte("A.")]
    cid = client.post("/conversations", json={"persona": "batman"}).json()["id"]
    _jouer(client, cid, "Ok.")
    reponse = client.post(f"/conversations/{cid}/clore")
    assert reponse.status_code == 200
    assert reponse.json()["episode_capture"] is False
    assert client.app.state.memoire.episodes == []


def test_l_episode_est_identifie_par_la_conversation_pas_le_persona(client):
    client.app.state.llm.tours = [TourTexte("Bien.")]
    cid = client.post("/conversations", json={"persona": "batman"}).json()["id"]
    _jouer(client, cid, "Une info durable.")
    client.post(f"/conversations/{cid}/clore")
    episode = client.app.state.memoire.episodes[0]
    assert episode.nom == cid
    assert episode.nom != "Batman"


def test_la_cloture_retire_la_conversation(client):
    client.app.state.llm.tours = [TourTexte("Bien.")]
    cid = client.post("/conversations", json={"persona": "batman"}).json()["id"]
    _jouer(client, cid, "Salut a toi.")
    client.post(f"/conversations/{cid}/clore")
    assert client.get(f"/conversations/{cid}").status_code == 404


def test_clore_une_conversation_inconnue_404(client):
    assert client.post("/conversations/inexistante/clore").status_code == 404


# --- Interruption (ADR 0012 décision 3) ------------------------------------


def test_l_interruption_tronque_le_dernier_tour_assistant_au_prefixe_prononce(client):
    client.app.state.llm.tours = [TourTexte("Phrase une. Phrase deux. Phrase trois.")]
    cid = client.post("/conversations", json={"persona": "batman"}).json()["id"]
    _jouer(client, cid, "Raconte-moi tout.")

    reponse = client.post(f"/conversations/{cid}/interrompre", json={"prefixe": "Phrase une."})
    assert reponse.status_code == 200
    assert reponse.json()["tronque"] is True

    historique = client.get(f"/conversations/{cid}").json()["historique"]
    dernier_assistant = [m for m in historique if m["role"] == "assistant"][-1]
    assert dernier_assistant["content"] == "Phrase une."


def test_l_interruption_sans_tour_assistant_ne_tronque_rien(client):
    cid = client.post("/conversations", json={"persona": "batman"}).json()["id"]
    reponse = client.post(f"/conversations/{cid}/interrompre", json={"prefixe": "quoi que ce soit"})
    assert reponse.status_code == 200
    assert reponse.json()["tronque"] is False


def test_interrompre_une_conversation_inconnue_404(client):
    reponse = client.post("/conversations/inexistante/interrompre", json={"prefixe": "x"})
    assert reponse.status_code == 404


def test_une_conversation_off_record_ne_capture_rien(personas_dir):
    (personas_dir / "fantome.md").write_text(
        "# Fantome (voix : Emma, off-record)\n\n```\nTu es discret.\n```\n",
        encoding="utf-8",
    )
    app = create_app(Settings(personas_dir=personas_dir))
    with TestClient(app) as client:
        app.state.llm.tours = [TourTexte("Compris.")]
        cid = client.post("/conversations", json={"persona": "fantome"}).json()["id"]
        client.post(f"/conversations/{cid}/tours", json={"texte": "Un secret durable."})
        reponse = client.post(f"/conversations/{cid}/clore")
        assert reponse.status_code == 200
        assert reponse.json()["episode_capture"] is False
        assert app.state.memoire.episodes == []
