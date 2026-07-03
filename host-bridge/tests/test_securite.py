"""Jeton partagé : le Pont écoute sur 0.0.0.0 en usage réel (host.docker.internal),
donc toute requête doit prouver qu'elle vient de la stack — sauf /health (healthchecks).
Jeton vide (défaut) = auth désactivée, comportement historique intact."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client_avec_jeton(catalog_path):
    app = create_app(
        Settings(runner="fake", player="fake", catalog_path=catalog_path, token="sesame")
    )
    with TestClient(app) as test_client:
        yield test_client


def test_sans_jeton_configure_tout_reste_libre(client):
    # La fixture `client` n'a pas de jeton : rien ne change pour le dev local.
    assert client.post("/actions/musique").status_code == 200


def test_requete_sans_jeton_est_refusee(client_avec_jeton):
    response = client_avec_jeton.post("/actions/musique")

    assert response.status_code == 401
    assert client_avec_jeton.app.state.runner.launched == []


def test_mauvais_jeton_est_refuse(client_avec_jeton):
    response = client_avec_jeton.post(
        "/actions/musique", headers={"X-Bridge-Token": "intrus"}
    )

    assert response.status_code == 401
    assert client_avec_jeton.app.state.runner.launched == []


def test_bon_jeton_passe(client_avec_jeton):
    response = client_avec_jeton.post(
        "/actions/musique", headers={"X-Bridge-Token": "sesame"}
    )

    assert response.status_code == 200
    assert [a.name for a in client_avec_jeton.app.state.runner.launched] == ["musique"]


def test_health_reste_libre_pour_les_healthchecks(client_avec_jeton):
    assert client_avec_jeton.get("/health").status_code == 200


def test_le_mcp_monte_est_couvert_aussi(client_avec_jeton):
    response = client_avec_jeton.post("/mcp", json={})

    assert response.status_code == 401
