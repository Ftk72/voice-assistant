import subprocess

import pytest

from app.config import Settings
from app.decodeurs.base import FormatAudioNonSupporte
from app.decodeurs.factory import build_decodeur
from app.decodeurs.fake import DecodeurFactice
from app.decodeurs.ffmpeg import DecodeurFfmpeg


def test_le_decodeur_factice_refuse_tout_non_wav():
    with pytest.raises(FormatAudioNonSupporte):
        DecodeurFactice().en_wav(b"des octets mp3")


def test_la_factory_choisit_le_factice_par_defaut():
    assert isinstance(build_decodeur(Settings()), DecodeurFactice)


def test_la_factory_choisit_ffmpeg_sur_reglage():
    assert isinstance(build_decodeur(Settings(decodeur="ffmpeg")), DecodeurFfmpeg)


def test_ffmpeg_appelle_le_binaire_et_renvoie_le_wav(monkeypatch):
    commande_vue = {}

    def faux_run(commande, **kwargs):
        commande_vue["commande"] = commande
        commande_vue["input"] = kwargs.get("input")
        return subprocess.CompletedProcess(commande, 0, stdout=b"RIFF....WAVE", stderr=b"")

    monkeypatch.setattr(subprocess, "run", faux_run)

    sortie = DecodeurFfmpeg().en_wav(b"des octets mp3")

    assert sortie == b"RIFF....WAVE"
    assert commande_vue["input"] == b"des octets mp3"
    assert "ffmpeg" in commande_vue["commande"][0]
    assert "pipe:0" in commande_vue["commande"]
    assert "pipe:1" in commande_vue["commande"]


def test_ffmpeg_traduit_un_echec_de_decodage(monkeypatch):
    def faux_run(commande, **kwargs):
        raise subprocess.CalledProcessError(1, commande, stderr=b"Invalid data")

    monkeypatch.setattr(subprocess, "run", faux_run)

    with pytest.raises(FormatAudioNonSupporte):
        DecodeurFfmpeg().en_wav(b"pas decodable")


def test_ffmpeg_absent_est_un_format_non_supporte(monkeypatch):
    def faux_run(commande, **kwargs):
        raise FileNotFoundError("ffmpeg")

    monkeypatch.setattr(subprocess, "run", faux_run)

    with pytest.raises(FormatAudioNonSupporte):
        DecodeurFfmpeg().en_wav(b"des octets mp3")
