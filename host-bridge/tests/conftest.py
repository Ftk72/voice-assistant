import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

CATALOGUE_DE_TEST = """
[actions.musique]
description = "Mettre la musique en pause ou la relancer"
linux = ["playerctl", "play-pause"]
windows = ["powershell", "-Command", "pause"]
"""


@pytest.fixture
def catalog_path(tmp_path):
    """Un petit catalogue sur disque : Settings a un catalog_path par défaut,
    les tests écrivent le leur dans tmp_path."""
    path = tmp_path / "catalog.toml"
    path.write_text(CATALOGUE_DE_TEST, encoding="utf-8")
    return path


@pytest.fixture
def client(catalog_path):
    app = create_app(Settings(runner="fake", player="fake", catalog_path=catalog_path))
    with TestClient(app) as test_client:
        yield test_client
