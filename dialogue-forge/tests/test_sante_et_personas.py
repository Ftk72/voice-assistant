def test_le_health_repond_ok(client):
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json() == {"status": "ok"}


def test_les_personas_sont_charges_au_bon_format(client):
    reponse = client.get("/personas")
    assert reponse.status_code == 200
    par_nom = {p["nom"]: p["voix"] for p in reponse.json()}
    # Le README et le fichier mal formé sont ignorés ; il reste deux personas.
    assert par_nom == {"Assistant": "Emma", "Batman": "Batman"}
