import pytest
from fastapi.testclient import TestClient

import app.main
from app.config import Settings
from app.graph.fake import InMemoryGraph
from app.main import build_graph, create_app


def test_le_backend_par_defaut_est_fake():
    assert isinstance(build_graph(Settings()), InMemoryGraph)


def test_le_lifespan_initialise_le_graphe_au_demarrage(monkeypatch):
    # Côté Graphiti, initialize() crée les index Neo4j (build_indices_and_constraints) :
    # sans cet appel au démarrage, chaque recherche logge une ClientError d'index manquant.
    class GrapheEspion(InMemoryGraph):
        def __init__(self):
            super().__init__()
            self.initialise = False

        async def initialize(self) -> None:
            self.initialise = True

    espion = GrapheEspion()
    monkeypatch.setattr(app.main, "build_graph", lambda settings: espion)
    with TestClient(create_app(Settings(backend="fake"))):
        assert espion.initialise


def test_le_backend_graphiti_echoue_proprement_sans_l_extra_installe():
    # graphiti-core n'est pas installé dans l'environnement de dev :
    # la sélection doit produire une erreur explicite, pas un crash obscur.
    with pytest.raises(RuntimeError, match="uv sync --extra graphiti"):
        build_graph(Settings(backend="graphiti"))
