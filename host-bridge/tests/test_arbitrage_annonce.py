"""Arbitrage de l'annonce entre la conversation et les enceintes (ticket 0044).

Une annonce jouée sur les enceintes pendant une conversation ouverte rentre par
le micro : l'assistant se répond à lui-même. Quand une conversation est ouverte,
l'annonce doit donc passer par le transport (flux WebRTC sortant, vu par l'AEC)
et **ne pas** toucher les enceintes.
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.conversation.base import CanalConversation
from app.conversation.fake import CanalFactice
from app.main import create_app

WAV = b"RIFF....WAVEfmt annonce"


@pytest.fixture
def client_avec_canal(catalog_path):
    """Fabrique un client dont le canal de conversation est remplaçable."""

    def fabriquer(canal: CanalConversation) -> TestClient:
        app = create_app(Settings(runner="fake", player="fake", catalog_path=catalog_path))
        app.state.canal_conversation = canal
        return TestClient(app)

    return fabriquer


def test_l_annonce_part_dans_la_conversation_quand_elle_est_ouverte(client_avec_canal):
    canal = CanalFactice(ouverte=True)
    with client_avec_canal(canal) as client:
        reponse = client.post("/play", content=WAV)

        assert reponse.status_code == 202
        assert canal.annonces == [WAV]
        # Le cœur du ticket : les enceintes sont restées muettes.
        assert client.app.state.player.played == []


def test_l_annonce_part_sur_les_enceintes_sans_conversation(client_avec_canal):
    canal = CanalFactice(ouverte=False)
    with client_avec_canal(canal) as client:
        reponse = client.post("/play", content=WAV)

        assert reponse.status_code == 202
        assert canal.annonces == []
        assert client.app.state.player.played == [WAV]


def test_l_annonce_se_replie_sur_les_enceintes_si_le_transport_refuse(client_avec_canal):
    # Conversation annoncée ouverte, mais le transport n'a plus de session au
    # moment de jouer (course entre les deux appels) : il refuse.
    canal = CanalFactice(ouverte=True, accepte=False)
    with client_avec_canal(canal) as client:
        reponse = client.post("/play", content=WAV)

        assert reponse.status_code == 202
        assert client.app.state.player.played == [WAV]


def test_l_annonce_se_replie_sur_les_enceintes_si_le_canal_leve(client_avec_canal, caplog):
    class CanalEnPanne(CanalConversation):
        async def conversation_ouverte(self) -> bool:
            raise RuntimeError("transport injoignable")

        async def jouer_annonce(self, wav: bytes) -> bool:
            raise RuntimeError("transport injoignable")

    with client_avec_canal(CanalEnPanne()) as client, caplog.at_level(logging.WARNING):
        reponse = client.post("/play", content=WAV)

        assert reponse.status_code == 202
        assert client.app.state.player.played == [WAV]
        assert any(enreg.levelno == logging.WARNING for enreg in caplog.records)
