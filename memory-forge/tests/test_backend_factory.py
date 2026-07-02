import pytest

from app.config import Settings
from app.graph.fake import InMemoryGraph
from app.main import build_graph


def test_le_backend_par_defaut_est_fake():
    assert isinstance(build_graph(Settings()), InMemoryGraph)


def test_le_backend_graphiti_echoue_proprement_sans_l_extra_installe():
    # graphiti-core n'est pas installé dans l'environnement de dev :
    # la sélection doit produire une erreur explicite, pas un crash obscur.
    with pytest.raises(RuntimeError, match="uv sync --extra graphiti"):
        build_graph(Settings(backend="graphiti"))
