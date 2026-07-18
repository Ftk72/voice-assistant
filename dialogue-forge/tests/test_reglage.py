"""Réglage grand public (ticket wayfinder 0014, modèle A) : persona + voix par
défaut, préférence **permanente** persistée sur disque. Toute nouvelle
conversation créée sans persona explicite adopte cette préférence."""

import json

from fastapi.testclient import TestClient

from app.llm.fake import TourTexte
from app.main import create_app


def _voix_des_phrases(reponse_tour):
    """Voix portées par les phrases du flux NDJSON d'un tour (cf. test_conversations)."""
    return [
        evenement["voix"]
        for ligne in reponse_tour.text.splitlines()
        if ligne
        for evenement in [json.loads(ligne)]
        if evenement["type"] == "phrase"
    ]


def test_la_preference_par_defaut_est_le_persona_par_defaut_sans_voix(client, settings):
    reponse = client.get("/reglage/preference")
    assert reponse.status_code == 200
    assert reponse.json() == {"persona": settings.persona_defaut, "voix": None}


def test_le_put_valide_enregistre_et_persiste(client, settings):
    reponse = client.put("/reglage/preference", json={"persona": "batman", "voix": "Emma"})
    assert reponse.status_code == 200
    assert reponse.json() == {"persona": "batman", "voix": "Emma"}

    # Persisté sur disque : une nouvelle app sur le même chemin la retrouve.
    contenu = json.loads(settings.reglage_path.read_text(encoding="utf-8"))
    assert contenu == {"persona": "batman", "voix": "Emma"}

    autre_app = create_app(settings)
    with TestClient(autre_app) as autre_client:
        assert autre_client.get("/reglage/preference").json() == {
            "persona": "batman",
            "voix": "Emma",
        }


def test_le_put_avec_un_persona_inconnu_est_refuse(client):
    reponse = client.put("/reglage/preference", json={"persona": "joker", "voix": None})
    assert reponse.status_code == 404


def test_une_conversation_sans_persona_adopte_la_preference_enregistree(client):
    client.put("/reglage/preference", json={"persona": "batman", "voix": "Emma"})

    client.app.state.llm.tours = [TourTexte("Une phrase.")]
    reponse_creation = client.post("/conversations", json={})
    assert reponse_creation.status_code == 201
    cid = reponse_creation.json()["id"]

    vue = client.get(f"/conversations/{cid}")
    assert vue.json()["persona"] == "Batman"

    reponse_tour = client.post(f"/conversations/{cid}/tours", json={"texte": "Parle."})
    assert _voix_des_phrases(reponse_tour) == ["Emma"]


def test_une_conversation_avec_persona_explicite_ignore_la_voix_preferee(client):
    # Préférence enregistrée : persona assistant, voix Emma. On crée pourtant
    # explicitement une conversation Batman : sa voix (Batman) doit primer,
    # la préférence ne s'impose que par défaut (persona non précisé).
    client.put("/reglage/preference", json={"persona": "assistant", "voix": "Emma"})

    client.app.state.llm.tours = [TourTexte("Une phrase.")]
    cid = client.post("/conversations", json={"persona": "batman"}).json()["id"]

    reponse_tour = client.post(f"/conversations/{cid}/tours", json={"texte": "Parle."})
    assert _voix_des_phrases(reponse_tour) == ["Batman"]
