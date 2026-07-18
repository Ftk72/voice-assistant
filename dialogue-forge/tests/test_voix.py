"""Catalogue de voix (ticket wayfinder 0014) : liste complète des voix
enrôlées et aperçu audio. Le menu ne doit jamais rester vide : en cas de panne
du catalogue, on replie sur les voix des personas."""

from fastapi.testclient import TestClient

from app.main import create_app
from app.voix.fake import CatalogueVoixFactice


def test_lister_les_voix_renvoie_le_catalogue(client):
    reponse = client.get("/voix")
    assert reponse.status_code == 200
    assert reponse.json() == {
        "voix": [
            {"id": "VoixDeTest", "nom": "VoixDeTest"},
            {"id": "Emma", "nom": "Emma"},
        ]
    }


def test_le_repli_renvoie_les_voix_des_personas_si_le_catalogue_echoue(settings):
    app = create_app(settings)
    app.state.catalogue_voix = CatalogueVoixFactice(echoue=True)
    with TestClient(app) as client:
        reponse = client.get("/voix")
        assert reponse.status_code == 200
        voix_renvoyees = {v["nom"] for v in reponse.json()["voix"]}
        # Les personas de test portent les voix Emma (assistant) et Batman.
        assert voix_renvoyees == {"Emma", "Batman"}


def test_l_apercu_d_une_voix_renvoie_un_wav(client):
    reponse = client.post("/voix/Emma/apercu")
    assert reponse.status_code == 200
    assert "audio/wav" in reponse.headers["content-type"]
    assert reponse.content.startswith(b"RIFF")


def test_l_apercu_indisponible_renvoie_502(settings):
    class CatalogueQuiEchoueAlApercu(CatalogueVoixFactice):
        async def apercu(self, voix_id: str) -> bytes:
            raise RuntimeError("Panne")

    app = create_app(settings)
    app.state.catalogue_voix = CatalogueQuiEchoueAlApercu()
    with TestClient(app) as client:
        reponse = client.post("/voix/Emma/apercu")
        assert reponse.status_code == 502
