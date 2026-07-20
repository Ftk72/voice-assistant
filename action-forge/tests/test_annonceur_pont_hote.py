"""L'annonceur réel doit présenter le jeton partagé au Pont hôte (X-Bridge-Token) :
le Pont écoute sur 0.0.0.0 en usage réel et refuse les requêtes sans jeton."""

import httpx

from app.annonce.pont_hote import AnnonceurPontHote
from app.config import Settings


def construire_annonceur(token: str, requetes: list[httpx.Request]) -> AnnonceurPontHote:
    async def repondre(request: httpx.Request) -> httpx.Response:
        requetes.append(request)
        return httpx.Response(200, content=b"RIFF....WAVEfmt ")

    settings = Settings(annonceur="pont_hote", host_bridge_token=token)
    client = httpx.AsyncClient(transport=httpx.MockTransport(repondre))
    return AnnonceurPontHote(settings, client=client)


async def test_le_jeton_part_avec_le_play():
    requetes: list[httpx.Request] = []
    annonceur = construire_annonceur("sesame", requetes)

    await annonceur.annoncer("Tâche terminée")

    play = [r for r in requetes if r.url.path == "/play"]
    assert len(play) == 1
    assert play[0].headers["X-Bridge-Token"] == "sesame"


async def test_sans_jeton_configure_pas_de_header():
    requetes: list[httpx.Request] = []
    annonceur = construire_annonceur("", requetes)

    await annonceur.annoncer("Tâche terminée")

    play = [r for r in requetes if r.url.path == "/play"]
    assert len(play) == 1
    assert "X-Bridge-Token" not in play[0].headers
