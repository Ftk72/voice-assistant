def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_events_et_timers_en_direct(client):
    assert client.get("/events").json() == []
    assert client.get("/timers").json() == []


def test_announce_passe_par_l_annonceur(client):
    response = client.post("/announce", json={"text": "Essai des enceintes."})

    assert response.status_code == 202
    announcer = client.app.state.announcer
    assert announcer.spoken == ["Essai des enceintes."]


def test_l_endpoint_mcp_est_monte(client):
    # Sans la poignée de main MCP le serveur refuse la requête,
    # mais la route doit exister (≠ 404).
    assert client.post("/mcp", json={}).status_code != 404
