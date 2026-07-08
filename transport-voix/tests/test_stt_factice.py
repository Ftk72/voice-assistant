import pytest

from app.stt.fake import STTFactice


@pytest.mark.asyncio
async def test_le_moteur_factice_transcrit_les_reponses_scriptees_puis_le_defaut():
    moteur = STTFactice(reponses=["Un.", "Deux."])

    assert await moteur.transcrire(b"audio-1") == "Un."
    assert await moteur.transcrire(b"audio-2") == "Deux."
    assert await moteur.transcrire(b"audio-3") == "Bonjour."
    assert moteur.appels == [b"audio-1", b"audio-2", b"audio-3"]
