import json
from pathlib import Path

import pytest

from app.providers.qwen3tts import Qwen3TTSProvider


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


def test_synthese_en_francais_sans_transcript_par_defaut(speaker_wav):
    engine = StubEngine()
    provider = Qwen3TTSProvider(engine_factory=lambda: engine)

    audio = provider.synthesize("Bonjour", speaker_wav)

    assert audio == b"RIFFfakeWAVE"
    assert engine.calls == [
        {
            "text": "Bonjour",
            "speaker_wav": speaker_wav,
            "language": "French",
            "ref_text": None,
        }
    ]


def test_config_json_de_la_voix_surcharge_langue_et_transcript(speaker_wav):
    (speaker_wav.parent / "config.json").write_text(
        json.dumps(
            {
                "language": "English",
                "ref_text": "Ce que dit l'échantillon.",
                "autre_cle": "ignorée",
            }
        )
    )
    engine = StubEngine()
    provider = Qwen3TTSProvider(engine_factory=lambda: engine)

    provider.synthesize("Hello", speaker_wav)

    call = engine.calls[0]
    assert call["language"] == "English"
    assert call["ref_text"] == "Ce que dit l'échantillon."
    assert "autre_cle" not in call


def test_le_repertoire_local_est_transmis_a_la_fabrique_par_defaut(tmp_path):
    """Sans engine_factory injecté, la fabrique par défaut doit transmettre
    model_dir au futur _RealQwen3TTSEngine — sans jamais l'instancier."""
    model_dir = tmp_path / "modele"

    provider = Qwen3TTSProvider(model_dir=model_dir)

    assert provider._engine_factory.keywords == {"model_dir": model_dir}


def test_le_moteur_n_est_charge_qu_a_la_premiere_synthese(speaker_wav):
    loads = []

    def factory():
        loads.append(1)
        return StubEngine()

    provider = Qwen3TTSProvider(engine_factory=factory)
    assert loads == []  # construction sans chargement

    provider.synthesize("Un", speaker_wav)
    provider.synthesize("Deux", speaker_wav)
    assert loads == [1]  # chargé une seule fois
