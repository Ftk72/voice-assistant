from conftest import add_voice


def test_les_voix_deposees_sont_listees_au_format_openwebui(client, voices_dir):
    add_voice(voices_dir, "Emma")
    add_voice(voices_dir, "Batman")

    response = client.get("/audio/voices")

    assert response.status_code == 200
    voices = response.json()["voices"]
    assert {"id": "Emma", "name": "Emma"} in voices
    assert {"id": "Batman", "name": "Batman"} in voices


def test_une_voix_deposee_apparait_sans_redemarrage(client, voices_dir):
    assert client.get("/audio/voices").json()["voices"] == []

    add_voice(voices_dir, "Emma")

    voices = client.get("/audio/voices").json()["voices"]
    assert voices == [{"id": "Emma", "name": "Emma"}]


def test_un_dossier_sans_speaker_wav_n_est_pas_une_voix(client, voices_dir):
    (voices_dir / "Incomplet").mkdir(parents=True)

    assert client.get("/audio/voices").json()["voices"] == []
