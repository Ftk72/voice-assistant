def test_atelier_repond_200_avec_le_html_attendu(client):
    reponse = client.get("/atelier")

    assert reponse.status_code == 200
    assert "text/html" in reponse.headers["content-type"]
    assert "/taches" in reponse.text
    assert "EventSource" in reponse.text
    assert "/annulation" in reponse.text
