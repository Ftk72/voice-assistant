"""Décodage du flux NDJSON du Dialogue Forge par le client REST.

Le contrat du DF est fixé ailleurs (cf. docstring de `rest.py`) ; ici on prouve
que chaque type d'événement du flux se décode dans le bon objet du port —
`phrase` → `Phrase`, `outil` → `AppelOutilVu`, `fin` → `FinTour`. Aucun réseau :
un `httpx.MockTransport` sert un flux scripté.
"""

import httpx

from app.dialogue.base import AppelOutilVu, FinTour, Phrase
from app.dialogue.rest import ClientDialogueREST


def _client_servant(lignes: list[str]) -> ClientDialogueREST:
    corps = ("\n".join(lignes) + "\n").encode()

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=corps, headers={"content-type": "application/x-ndjson"}
        )

    client = ClientDialogueREST("http://df.test")
    client._client = httpx.AsyncClient(
        base_url="http://df.test", transport=httpx.MockTransport(handler)
    )
    return client


async def test_le_flux_decode_phrases_outils_et_fin_dans_l_ordre():
    client = _client_servant(
        [
            '{"type":"phrase","texte":"Une seconde.","voix":"Emma"}',
            '{"type":"outil","nom":"meteo"}',
            '{"type":"phrase","texte":"Il fait beau.","voix":"Emma"}',
            '{"type":"fin","reponse":"Une seconde. Il fait beau."}',
        ]
    )

    evenements = [e async for e in client.jouer_tour("c1", "quel temps fait-il ?")]
    await client.aclose()

    assert evenements == [
        Phrase(texte="Une seconde.", voix="Emma"),
        AppelOutilVu(nom="meteo"),
        Phrase(texte="Il fait beau.", voix="Emma"),
        FinTour(reponse="Une seconde. Il fait beau."),
    ]
