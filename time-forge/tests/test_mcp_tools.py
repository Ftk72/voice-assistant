import pytest

from app.announce.log import LogAnnouncer
from app.mcp_server import build_mcp
from app.store.memory import InMemoryAgenda
from app.timers import TimerBoard


@pytest.fixture
def mcp():
    return build_mcp(InMemoryAgenda(), TimerBoard(LogAnnouncer()))


async def call_tool(mcp, name: str, arguments: dict) -> str:
    result = await mcp.call_tool(name, arguments)
    content = result[0] if isinstance(result, tuple) else result
    return content[0].text


async def test_create_event_confirme_en_clair(mcp):
    answer = await call_tool(
        mcp,
        "create_event",
        {"title": "Dentiste", "when": "2026-07-08T15:00", "announce_lead_minutes": 60},
    )

    assert "Dentiste" in answer
    assert "60 min avant" in answer


async def test_un_rappel_est_un_evenement_annonce_a_l_heure_dite(mcp):
    answer = await call_tool(
        mcp,
        "create_event",
        {"title": "Appeler le plombier", "when": "2026-07-08T09:00", "announce_lead_minutes": 0},
    )

    assert "annoncé à l'heure dite" in answer


async def test_list_events_pour_un_jour(mcp):
    await call_tool(mcp, "create_event", {"title": "Dentiste", "when": "2026-07-08T15:00"})
    await call_tool(mcp, "create_event", {"title": "Autre jour", "when": "2026-07-09T15:00"})

    answer = await call_tool(mcp, "list_events", {"day": "2026-07-08"})

    assert "Dentiste" in answer
    assert "Autre jour" not in answer


async def test_delete_event_par_id(mcp):
    created = await call_tool(
        mcp, "create_event", {"title": "À annuler", "when": "2026-07-08T15:00"}
    )
    event_id = created.split("id ")[1].split(")")[0]

    answer = await call_tool(mcp, "delete_event", {"event_id": event_id})

    assert "supprimé" in answer.lower()


async def test_set_puis_cancel_timer(mcp):
    answer = await call_tool(mcp, "set_timer", {"label": "pâtes", "seconds": 480})
    assert "pâtes" in answer

    listing = await call_tool(mcp, "list_timers", {})
    assert "pâtes" in listing

    cancelled = await call_tool(mcp, "cancel_timer", {"label": "pâtes"})
    assert "annulé" in cancelled

    assert "aucun" in (await call_tool(mcp, "list_timers", {})).lower()


def test_l_endpoint_mcp_est_monte(client):
    # Sans la poignée de main MCP le serveur refuse la requête,
    # mais la route doit exister (≠ 404).
    assert client.post("/mcp", json={}).status_code != 404


def test_l_endpoint_mcp_accepte_le_host_du_reseau_docker(client):
    # La protection anti-DNS-rebinding du SDK MCP n'accepte par défaut que
    # localhost/127.0.0.1 : depuis le réseau Docker, OpenWebUI arrive avec
    # Host « time:8400 » et prenait un 421 Misdirected Request (2026-07-06).
    response = client.post(
        "/mcp/",
        headers={
            "Host": "time:8400",
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
