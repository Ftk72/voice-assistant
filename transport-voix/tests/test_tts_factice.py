import pytest

from app.tts.fake import TTSFactice


@pytest.mark.asyncio
async def test_le_moteur_factice_synthetise_et_journalise_les_appels():
    moteur = TTSFactice()

    audio = await moteur.synthetiser("Bonjour.", voix="Emma")

    assert audio == b"Bonjour."
    assert moteur.appels == [("Bonjour.", "Emma")]
