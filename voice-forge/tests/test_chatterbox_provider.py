import json
from pathlib import Path

import pytest

from app.providers.chatterbox import ChatterboxProvider


class StubEngine:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def synthesize_wav(self, text: str, speaker_wav: Path, **params) -> bytes:
        self.calls.append({"text": text, "speaker_wav": speaker_wav, **params})
        return b"RIFFfakeWAVE"


@pytest.fixture
def speaker_wav(tmp_path: Path) -> Path:
    voice = tmp_path / "Emma"
    voice.mkdir()
    wav = voice / "speaker.wav"
    wav.write_bytes(b"RIFF")
    return wav


def test_synthese_en_francais_par_defaut(speaker_wav):
    engine = StubEngine()
    provider = ChatterboxProvider(engine_factory=lambda: engine)

    audio = provider.synthesize("Bonjour", speaker_wav)

    assert audio == b"RIFFfakeWAVE"
    assert engine.calls == [
        {
            "text": "Bonjour",
            "speaker_wav": speaker_wav,
            "language": "fr",
            "exaggeration": 0.5,
            "cfg_weight": 0.5,
        }
    ]


def test_config_json_de_la_voix_surcharge_les_parametres(speaker_wav):
    (speaker_wav.parent / "config.json").write_text(
        json.dumps({"language": "en", "exaggeration": 0.9, "autre_cle": "ignorée"})
    )
    engine = StubEngine()
    provider = ChatterboxProvider(engine_factory=lambda: engine)

    provider.synthesize("Hello", speaker_wav)

    call = engine.calls[0]
    assert call["language"] == "en"
    assert call["exaggeration"] == 0.9
    assert call["cfg_weight"] == 0.5  # non surchargé → défaut
    assert "autre_cle" not in call


def test_le_repertoire_local_est_transmis_a_la_fabrique_par_defaut(tmp_path):
    """Sans engine_factory injecté, la fabrique par défaut doit transmettre
    chatterbox_dir au futur _RealChatterboxEngine — sans jamais l'instancier."""
    chatterbox_dir = tmp_path / "modele"

    provider = ChatterboxProvider(chatterbox_dir=chatterbox_dir)

    assert provider._engine_factory.keywords == {"local_dir": chatterbox_dir}


def test_sans_repertoire_local_la_fabrique_par_defaut_transmet_none():
    provider = ChatterboxProvider()

    assert provider._engine_factory.keywords == {"local_dir": None}


def test_le_moteur_n_est_charge_qu_a_la_premiere_synthese(speaker_wav):
    loads = []

    def factory():
        loads.append(1)
        return StubEngine()

    provider = ChatterboxProvider(engine_factory=factory)
    assert loads == []  # construction sans chargement

    provider.synthesize("Un", speaker_wav)
    provider.synthesize("Deux", speaker_wav)
    assert loads == [1]  # chargé une seule fois
