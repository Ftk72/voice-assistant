import pytest

from app.mcp_server import build_mcp
from app.schemas import PageText
from app.world.fake import FakeWorld


@pytest.fixture
def world():
    return FakeWorld()


async def call_tool(mcp, name: str, arguments: dict) -> str:
    result = await mcp.call_tool(name, arguments)
    content = result[0] if isinstance(result, tuple) else result
    return content[0].text


async def test_web_search_renvoie_des_extraits_sources(world):
    mcp = build_mcp(world)

    answer = await call_tool(mcp, "web_search", {"query": "python 3.13"})

    assert "Python 3.13" in answer
    assert "https://docs.python.org/3.13/whatsnew/" in answer  # la source est là


async def test_web_search_sans_resultat_le_dit(world):
    world.results = []
    mcp = build_mcp(world)

    answer = await call_tool(mcp, "web_search", {"query": "xyzzy"})

    assert "aucun" in answer.lower()


async def test_weather_est_parlable(world):
    mcp = build_mcp(world)

    answer = await call_tool(mcp, "weather", {"place": "Lyon", "days": 2})

    assert "Lyon" in answer
    assert "ciel dégagé" in answer
    assert "degrés" in answer


async def test_briefing_regroupe_par_source(world):
    mcp = build_mcp(world)

    answer = await call_tool(mcp, "briefing", {})

    assert "[Le Monde]" in answer
    assert "Titre factice du jour" in answer


async def test_briefing_sans_flux_le_dit(world):
    world.items = []
    mcp = build_mcp(world)

    answer = await call_tool(mcp, "briefing", {})

    assert "aucun" in answer.lower()


async def test_read_page_signale_la_troncature(world):
    world.pages["https://exemple.fr/long"] = PageText(
        url="https://exemple.fr/long", title="Long", text="Début du texte…", truncated=True
    )
    mcp = build_mcp(world)

    answer = await call_tool(mcp, "read_page", {"url": "https://exemple.fr/long"})

    assert "Début du texte…" in answer
    assert "tronqué" in answer.lower()
