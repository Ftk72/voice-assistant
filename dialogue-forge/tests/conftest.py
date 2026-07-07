import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app

PERSONA_ASSISTANT = """# Assistant (voix : Emma)

```
Tu es un assistant vocal francophone. Sois bref et parle comme on parle.
```
"""

PERSONA_BATMAN = """# Batman (voix : Batman)

```
Tu es Batman. Laconique et grave.
```
"""

PERSONA_MAL_FORME = """Pas de titre valable ici, et aucun bloc de code.
"""


@pytest.fixture
def personas_dir(tmp_path):
    """Dossier de personas au format du dépôt, plus un README et un fichier mal
    formé à ignorer proprement."""
    (tmp_path / "assistant.md").write_text(PERSONA_ASSISTANT, encoding="utf-8")
    (tmp_path / "batman.md").write_text(PERSONA_BATMAN, encoding="utf-8")
    (tmp_path / "README.md").write_text("# À ignorer", encoding="utf-8")
    (tmp_path / "casse.md").write_text(PERSONA_MAL_FORME, encoding="utf-8")
    return tmp_path


@pytest.fixture
def settings(personas_dir):
    return Settings(personas_dir=personas_dir)


@pytest.fixture
def client(settings):
    app = create_app(settings)
    # Le `with` exécute le lifespan.
    with TestClient(app) as test_client:
        yield test_client
