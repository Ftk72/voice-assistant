"""Le module d'interface du dialogue (A4) : page servie par le Dialogue Forge,
chargée en onglet console (ADR 0009 — chaque forge sert sa propre UI). On ne
teste ici que le **service** de la page et de ses assets ; le comportement vif
(fil de conversation alimenté par le relais RTVI) se vérifie côté coquille."""


def test_la_page_du_module_dialogue_est_servie(client):
    reponse = client.get("/dialogue")
    assert reponse.status_code == 200
    assert "text/html" in reponse.headers["content-type"]
    # La page charge son script et son style (assets servis par la même route).
    corps = reponse.text
    assert "dialogue.js" in corps
    assert "dialogue.css" in corps


def test_les_assets_du_module_sont_servis(client):
    js = client.get("/dialogue/dialogue.js")
    assert js.status_code == 200
    assert "javascript" in js.headers["content-type"]

    css = client.get("/dialogue/dialogue.css")
    assert css.status_code == 200
    assert "css" in css.headers["content-type"]
