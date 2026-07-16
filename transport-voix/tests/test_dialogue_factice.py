import pytest

from app.dialogue.base import FinTour, Phrase
from app.dialogue.fake import ClientDialogueFactice


@pytest.mark.asyncio
async def test_jouer_tour_emet_des_phrases_avec_voix_puis_une_fin_de_tour():
    client_dialogue = ClientDialogueFactice()
    conversation = await client_dialogue.creer_conversation()

    evenements = [e async for e in client_dialogue.jouer_tour(conversation, "Salut")]

    *phrases, fin = evenements
    assert phrases
    assert all(isinstance(p, Phrase) and p.voix == "Emma" for p in phrases)
    assert isinstance(fin, FinTour)


@pytest.mark.asyncio
async def test_interrompre_et_clore_sont_journalises():
    client_dialogue = ClientDialogueFactice()
    conversation = await client_dialogue.creer_conversation()

    await client_dialogue.interrompre(conversation, "Bonjour, comment")
    episode_capture = await client_dialogue.clore(conversation)

    assert client_dialogue.interruptions == [(conversation, "Bonjour, comment")]
    assert client_dialogue.clotures == [conversation]
    assert episode_capture is True


def test_le_client_rest_a_un_timeout_de_lecture_genereux():
    """Le défaut httpx (5 s) tuait le stream du premier tour à froid
    (prefill LLM > 5 s) — le timeout de lecture doit rester large."""
    from app.dialogue.rest import ClientDialogueREST

    client = ClientDialogueREST("http://127.0.0.1:8600")
    assert client._client.timeout.read >= 60
    assert client._client.timeout.connect <= 15
