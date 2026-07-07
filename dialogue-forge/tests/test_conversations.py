def test_creation_de_conversation_avec_persona(client):
    reponse = client.post("/conversations", json={"persona": "batman"})
    assert reponse.status_code == 201
    identifiant = reponse.json()["id"]

    vue = client.get(f"/conversations/{identifiant}")
    assert vue.status_code == 200
    assert vue.json()["persona"] == "Batman"
    assert vue.json()["historique"] == []


def test_creation_avec_persona_par_defaut(client):
    reponse = client.post("/conversations", json={})
    assert reponse.status_code == 201
    identifiant = reponse.json()["id"]
    assert client.get(f"/conversations/{identifiant}").json()["persona"] == "Assistant"


def test_persona_inconnu_refuse(client):
    assert client.post("/conversations", json={"persona": "joker"}).status_code == 404


def test_conversation_inconnue_404(client):
    assert client.get("/conversations/inexistante").status_code == 404
    tour = client.post("/conversations/inexistante/tours", json={"texte": "Salut"})
    assert tour.status_code == 404
