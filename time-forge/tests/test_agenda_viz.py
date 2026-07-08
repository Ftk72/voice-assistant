"""Page de visualisation agenda + minuteurs (roadmap B3) — module d'interface
servi par time-forge, imite le pattern /viz de memory-forge."""


def test_la_page_agenda_est_servie(client):
    reponse = client.get("/agenda")
    assert reponse.status_code == 200
    assert "text/html" in reponse.headers["content-type"]
    corps = reponse.text
    assert "Agenda" in corps
    assert "Minuteurs" in corps


def test_la_page_agenda_consomme_les_endpoints_existants(client):
    corps = client.get("/agenda").text
    assert "/events" in corps
    assert "/timers" in corps
