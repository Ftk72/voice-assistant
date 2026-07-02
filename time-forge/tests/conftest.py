import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client():
    app = create_app(Settings(store="memory", announcer="log"))
    # Le `with` exécute le lifespan (boucle d'agenda + session MCP).
    with TestClient(app) as test_client:
        yield test_client
