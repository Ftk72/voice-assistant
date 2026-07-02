import pytest

from app.actions.fake import FakeRunner
from app.catalog import Action
from app.mcp_server import build_mcp


@pytest.fixture
def runner():
    return FakeRunner()


@pytest.fixture
def catalog():
    return {
        "musique": Action(
            name="musique",
            description="Mettre la musique en pause",
            linux=["playerctl", "play-pause"],
        )
    }


async def call_tool(mcp, name: str, arguments: dict) -> str:
    result = await mcp.call_tool(name, arguments)
    content = result[0] if isinstance(result, tuple) else result
    return content[0].text


async def test_list_actions_propose_nom_et_description(catalog, runner):
    mcp = build_mcp(catalog, runner)

    answer = await call_tool(mcp, "list_actions", {})

    assert "musique" in answer
    assert "Mettre la musique en pause" in answer


async def test_run_action_lance_l_action(catalog, runner):
    mcp = build_mcp(catalog, runner)

    answer = await call_tool(mcp, "run_action", {"name": "musique"})

    assert "fait" in answer.lower()
    assert [a.name for a in runner.launched] == ["musique"]


async def test_run_action_hors_liste_blanche_refuse_sans_rien_lancer(catalog, runner):
    mcp = build_mcp(catalog, runner)

    answer = await call_tool(mcp, "run_action", {"name": "rm -rf /"})

    assert "liste blanche" in answer.lower()
    # Rien n'a été lancé : le refus est total.
    assert runner.launched == []
