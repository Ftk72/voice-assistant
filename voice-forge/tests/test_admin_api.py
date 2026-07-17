from conftest import add_voice

from app.decodeurs.base import FormatAudioNonSupporte


def import_voice(client, name: str):
    return client.post(
        "/admin/api/voices",
        data={"name": name},
        files={"speaker": ("sample.wav", b"RIFFxxxxWAVE", "audio/wav")},
    )


def import_fichier(client, name: str, contenu: bytes, nom_fichier: str):
    return client.post(
        "/admin/api/voices",
        data={"name": name},
        files={"speaker": (nom_fichier, contenu, "application/octet-stream")},
    )


class DecodeurEspion:
    """Décodeur de test : enregistre ses appels, renvoie un WAV canné ou lève."""

    def __init__(self, sortie: bytes | None = b"RIFFdecodeWAVE") -> None:
        self.appels: list[bytes] = []
        self._sortie = sortie

    def en_wav(self, donnees: bytes) -> bytes:
        self.appels.append(donnees)
        if self._sortie is None:
            raise FormatAudioNonSupporte("espion")
        return self._sortie


def test_importer_une_voix_la_rend_visible(client):
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


def test_un_wav_est_stocke_tel_quel_sans_passer_par_le_decodeur(client, voices_dir):
    espion = DecodeurEspion()
    client.app.state.decodeur = espion

    assert import_voice(client, "Emma").status_code == 201
    assert espion.appels == []  # le WAV court-circuite le décodeur
    assert (voices_dir / "Emma" / "speaker.wav").read_bytes() == b"RIFFxxxxWAVE"


def test_un_mp3_est_decode_en_wav_puis_stocke(client, voices_dir):
    espion = DecodeurEspion(sortie=b"RIFFdecodeWAVE")
    client.app.state.decodeur = espion

    response = import_fichier(client, "Emma", b"ID3 octets mp3", "voix.mp3")

    assert response.status_code == 201
    assert espion.appels == [b"ID3 octets mp3"]  # le décodeur a reçu les octets bruts
    assert (voices_dir / "Emma" / "speaker.wav").read_bytes() == b"RIFFdecodeWAVE"
    assert client.get("/audio/voices").json()["voices"] == [{"id": "Emma", "name": "Emma"}]


def test_un_format_indecodable_renvoie_415(client):
    client.app.state.decodeur = DecodeurEspion(sortie=None)  # lève FormatAudioNonSupporte

    assert import_fichier(client, "Emma", b"octets illisibles", "voix.xyz").status_code == 415


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
