"""Page du réglage grand public (ticket wayfinder 0014) : on ne teste ici que
le **service** de la page et de ses assets, façon test_module_interface.py."""


def test_la_page_de_reglage_est_servie(client):
    reponse = client.get("/reglage")
    assert reponse.status_code == 200
    assert "text/html" in reponse.headers["content-type"]
    corps = reponse.text
    assert "reglage.js" in corps
    assert "reglage.css" in corps


def test_les_assets_du_reglage_sont_servis(client):
    js = client.get("/reglage/reglage.js")
    assert js.status_code == 200
    assert "javascript" in js.headers["content-type"]

    css = client.get("/reglage/reglage.css")
    assert css.status_code == 200
    assert "css" in css.headers["content-type"]
