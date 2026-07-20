import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client_bavard():
    """Une forge dont le LLM factice répond en un seul pas — le pattern le plus
    simple pour exercer l'API sans dépendre du budget de pas."""
    settings = Settings(atelier_backend="fake")
    app = create_app(settings)
    with TestClient(app) as test_client:
        yield test_client


def test_confier_une_tache_rend_202_et_la_tache_en_cours(client_bavard):
    reponse = client_bavard.post("/taches", json={"enonce": "dis bonjour"})

    assert reponse.status_code == 202
    corps = reponse.json()
    assert corps["enonce"] == "dis bonjour"
    assert corps["statut"] in ("en_cours", "terminee")
    assert "id" in corps


def test_obtenir_une_tache_par_id(client_bavard):
    creee = client_bavard.post("/taches", json={"enonce": "dis bonjour"}).json()

    reponse = client_bavard.get(f"/taches/{creee['id']}")

    assert reponse.status_code == 200
    assert reponse.json()["id"] == creee["id"]


def test_obtenir_une_tache_inconnue_rend_404(client_bavard):
    reponse = client_bavard.get("/taches/inconnue")

    assert reponse.status_code == 404


def test_lister_les_taches(client_bavard):
    id1 = client_bavard.post("/taches", json={"enonce": "un"}).json()["id"]
    id2 = client_bavard.post("/taches", json={"enonce": "deux"}).json()["id"]

    reponse = client_bavard.get("/taches")

    ids = {t["id"] for t in reponse.json()}
    assert {id1, id2} <= ids


def test_annuler_une_tache_inconnue_rend_404(client_bavard):
    reponse = client_bavard.post("/taches/inconnue/annulation")

    assert reponse.status_code == 404
