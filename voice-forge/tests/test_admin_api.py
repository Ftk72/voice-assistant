from conftest import add_voice


def import_voice(client, name: str):
    return client.post(
        "/admin/api/voices",
        data={"name": name},
        files={"speaker": ("sample.wav", b"RIFFxxxxWAVE", "audio/wav")},
    )


def test_importer_une_voix_la_rend_visible_dans_openwebui(client):
    response = import_voice(client, "Emma")

    assert response.status_code == 201
    assert client.get("/audio/voices").json()["voices"] == [{"id": "Emma", "name": "Emma"}]


def test_importer_un_nom_deja_pris_renvoie_409(client):
    import_voice(client, "Emma")

    assert import_voice(client, "Emma").status_code == 409


def test_importer_un_fichier_qui_n_est_pas_un_wav_renvoie_415(client):
    response = client.post(
        "/admin/api/voices",
        data={"name": "Emma"},
        files={"speaker": ("sample.wav", b"pas un wav", "audio/wav")},
    )

    assert response.status_code == 415


def test_les_noms_dangereux_sont_rejetes(client):
    for name in ["../evil", "a/b", "", "x" * 51]:
        assert import_voice(client, name).status_code == 422, name


def test_supprimer_une_voix(client, voices_dir):
    add_voice(voices_dir, "Emma")

    response = client.delete("/admin/api/voices/Emma")

    assert response.status_code == 204
    assert client.get("/audio/voices").json()["voices"] == []


def test_supprimer_une_voix_inconnue_renvoie_404(client):
    assert client.delete("/admin/api/voices/Inconnue").status_code == 404


def test_apercu_d_une_voix_renvoie_l_audio(client, voices_dir):
    add_voice(voices_dir, "Emma")

    response = client.post("/admin/api/voices/Emma/preview", json={"text": "Bonjour"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert response.content[:4] == b"RIFF"


def test_la_page_d_admin_est_servie(client):
    response = client.get("/admin")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Voice Forge" in response.text
