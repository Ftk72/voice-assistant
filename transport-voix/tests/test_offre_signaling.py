"""La route de signaling /offer et le client de prototypage.

Le pipeline Pipecat lui-même est « jamais exécuté » (extra `pipecat` non
installé) : ces tests couvrent ce qui l'est sans Pipecat — le garde-fou du
chemin factice et la présence du client navigateur."""


def test_offer_repond_503_sans_transport_pipecat(client):
    # Config par défaut = transport factice : aucune session temps réel possible.
    reponse = client.post("/offer", json={"sdp": "v=0", "type": "offer"})
    assert reponse.status_code == 503


def test_la_racine_redirige_vers_le_prototype(client):
    reponse = client.get("/", follow_redirects=False)
    assert reponse.status_code == 307
    assert reponse.headers["location"] == "/prototype"


def test_le_client_de_prototypage_est_servi(client):
    reponse = client.get("/prototype")
    assert reponse.status_code == 200
    assert "text/html" in reponse.headers["content-type"]
    # C'est bien le client WebRTC (getUserMedia + POST /offer), pas une page vide.
    assert "getUserMedia" in reponse.text
    assert "/offer" in reponse.text
