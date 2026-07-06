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


def test_l_endpoint_mcp_est_monte(client):
    # Sans la poignée de main MCP le serveur refuse la requête,
    # mais la route doit exister (≠ 404).
    assert client.post("/mcp", json={}).status_code != 404


def test_l_endpoint_mcp_accepte_le_host_du_reseau_docker(client):
    # La protection anti-DNS-rebinding du SDK MCP n'accepte par défaut que
    # localhost/127.0.0.1 : depuis le réseau Docker, OpenWebUI arrive avec
    # Host « world:8300 » et prenait un 421 Misdirected Request (2026-07-06).
    response = client.post(
        "/mcp/",
        headers={
            "Host": "world:8300",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        },
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            },
        },
    )
    assert response.status_code == 200
