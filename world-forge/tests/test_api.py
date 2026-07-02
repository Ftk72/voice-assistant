def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_search_direct_pour_smoke_test(client):
    response = client.get("/search", params={"q": "python"})

    assert response.status_code == 200
    assert response.json()[0]["url"].startswith("https://")


def test_weather_direct(client):
    response = client.get("/weather", params={"place": "Lyon", "days": 3})

    assert response.status_code == 200
    body = response.json()
    assert body["place"] == "Lyon"
    assert len(body["days"]) == 3


def test_l_endpoint_mcp_est_monte(client):
    # Sans la poignée de main MCP le serveur refuse la requête,
    # mais la route doit exister (≠ 404).
    assert client.post("/mcp", json={}).status_code != 404
