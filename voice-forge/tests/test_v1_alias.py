from conftest import add_voice


def test_les_endpoints_repondent_aussi_sous_le_prefixe_v1(client, voices_dir):
    add_voice(voices_dir, "Emma")

    assert client.get("/v1/audio/voices").json() == client.get("/audio/voices").json()

    response = client.post(
        "/v1/audio/speech",
        json={"model": "tts-1", "input": "Bonjour", "voice": "Emma"},
    )
    assert response.status_code == 200
    assert response.content[:4] == b"RIFF"
