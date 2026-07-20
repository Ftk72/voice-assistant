"""Le transport expose l'état de conversation et sait jouer une annonce.

Ticket wayfinder 0044 : le Pont hôte arbitre où sort une annonce. Il a besoin
de deux choses du transport — savoir si une conversation est ouverte, et
pouvoir lui confier un WAV pour qu'il parte dans le flux WebRTC sortant (seul
chemin que l'annulation d'écho de la coquille sait soustraire du micro).
"""

WAV = b"RIFF....WAVEfmt annonce"


def test_conversation_signale_l_etat_ferme_du_transport(client):
    reponse = client.get("/conversation")

    assert reponse.status_code == 200
    assert reponse.json() == {"ouverte": False}


def test_conversation_signale_l_etat_ouvert_du_transport(client):
    client.app.state.transport.ouverte = True

    reponse = client.get("/conversation")

    assert reponse.status_code == 200
    assert reponse.json() == {"ouverte": True}


def test_l_annonce_est_injectee_quand_une_conversation_est_ouverte(client):
    client.app.state.transport.ouverte = True

    reponse = client.post("/annonce", content=WAV)

    assert reponse.status_code == 202
    assert client.app.state.transport.annonces_jouees == [WAV]


def test_l_annonce_est_refusee_sans_conversation_ouverte(client):
    reponse = client.post("/annonce", content=WAV)

    assert reponse.status_code == 409
    assert client.app.state.transport.annonces_jouees == []
