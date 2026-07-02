from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def voices_dir(tmp_path: Path) -> Path:
    return tmp_path / "voices"


@pytest.fixture
def client(voices_dir: Path) -> TestClient:
    app = create_app(Settings(voices_dir=voices_dir))
    return TestClient(app)


def add_voice(voices_dir: Path, name: str) -> None:
    """Simule le dépôt d'un dossier de voix : voices/Nom/speaker.wav."""
    voice = voices_dir / name
    voice.mkdir(parents=True)
    (voice / "speaker.wav").write_bytes(b"RIFF")
