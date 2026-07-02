from conftest import add_voice


def test_speech_renvoie_un_wav_pour_une_voix_connue(client, voices_dir):
    add_voice(voices_dir, "Emma")

    response = client.post(
        "/audio/speech",
        json={"model": "tts-1", "input": "Bonjour le monde", "voice": "Emma"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content[:4] == b"RIFF"
    assert response.content[8:12] == b"WAVE"


def test_speech_avec_voix_inconnue_renvoie_400(client):
    response = client.post(
        "/audio/speech",
        json={"model": "tts-1", "input": "Bonjour", "voice": "Inexistante"},
    )

    assert response.status_code == 400
    assert "Inexistante" in response.json()["detail"]
