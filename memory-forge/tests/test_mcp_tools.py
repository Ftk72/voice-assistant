import pytest

from app.graph.fake import InMemoryGraph
from app.insight.fake import GenerateurInsightFactice
from app.mcp_server import build_mcp
from app.schemas import EpisodeIn


@pytest.fixture
async def graph():
    graph = InMemoryGraph()
    await graph.add_episode(
        EpisodeIn(content="Léa fait du judo.", source="conversation", name="appel du 2026-07-01")
    )
    return graph


async def call_tool(mcp, name: str, arguments: dict) -> str:
    result = await mcp.call_tool(name, arguments)
    content = result[0] if isinstance(result, tuple) else result
    return content[0].text


async def test_recall_renvoie_les_faits_avec_leur_provenance(graph):
    mcp = build_mcp(graph, GenerateurInsightFactice())

    answer = await call_tool(mcp, "recall", {"query": "judo"})

    assert "Léa fait du judo." in answer
    assert "appel du 2026-07-01" in answer


async def test_recall_sans_resultat_le_dit_explicitement(graph):
    mcp = build_mcp(graph, GenerateurInsightFactice())

    answer = await call_tool(mcp, "recall", {"query": "escalade"})

    assert "aucun" in answer.lower()


async def test_forget_supprime_et_annonce_le_compte(graph):
    mcp = build_mcp(graph, GenerateurInsightFactice())

    answer = await call_tool(mcp, "forget", {"entity": "Léa"})

    assert "1" in answer
    assert await graph.search("judo") == []


async def test_raconter_memoire_renvoie_un_paragraphe(graph):
    mcp = build_mcp(graph, GenerateurInsightFactice())

    answer = await call_tool(mcp, "raconter_memoire", {})

    assert answer.strip() != ""


def test_l_endpoint_mcp_est_monte(client):
    # Sans la poignée de main MCP le serveur refuse la requête,
    # mais la route doit exister (≠ 404).
    assert client.post("/mcp", json={}).status_code != 404


def test_l_endpoint_mcp_accepte_le_host_du_reseau_docker(client):
    # La protection anti-DNS-rebinding du SDK MCP n'accepte par défaut que
    # localhost/127.0.0.1 : depuis le réseau Docker, OpenWebUI arrive avec
    # Host « memory:8200 » et prenait un 421 Misdirected Request (2026-07-06).
    response = client.post(
        "/mcp/",
        headers={
            "Host": "memory:8200",
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
