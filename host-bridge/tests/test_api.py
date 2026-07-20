def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    # `/health` porte aussi le canal d'annonce retenu (ticket 0044) : c'est le
    # seul moyen de distinguer au curl un Pont correctement lancé d'un Pont
    # dégradé en `fake`, qui joue tout sur les enceintes sans rien signaler.
    assert response.json() == {"status": "ok", "canal_conversation": "fake"}


def test_get_actions_liste_le_catalogue_sans_argv(client):
    response = client.get("/actions")

    assert response.status_code == 200
    body = response.json()
    assert body == [{"name": "musique", "description": "Mettre la musique en pause ou la relancer"}]


def test_post_action_lance_via_le_runner(client):
    response = client.post("/actions/musique")

    assert response.status_code == 200
    assert [a.name for a in client.app.state.runner.launched] == ["musique"]


def test_post_action_hors_catalogue_404(client):
    response = client.post("/actions/inexistante")

    assert response.status_code == 404
    assert client.app.state.runner.launched == []


def test_play_alimente_le_player(client):
    wav = b"RIFF....WAVEfmt "

    response = client.post("/play", content=wav)

    assert response.status_code == 202
    assert client.app.state.player.played == [wav]


def test_l_endpoint_mcp_est_monte(client):
    # Sans la poignée de main MCP le serveur refuse la requête,
    # mais la route doit exister (≠ 404).
    assert client.post("/mcp", json={}).status_code != 404
