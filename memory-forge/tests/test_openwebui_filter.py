import importlib.util
import sys
from pathlib import Path

import pytest

FILTER_PATH = Path(__file__).parents[2] / "openwebui" / "functions" / "memory_filter.py"


@pytest.fixture
def memory_filter():
    spec = importlib.util.spec_from_file_location("memory_filter", FILTER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["memory_filter"] = module
    spec.loader.exec_module(module)
    return module.Filter()


def body_with(*messages: dict) -> dict:
    return {"messages": list(messages), "chat_id": "chat-42"}


async def test_inlet_injecte_les_faits_en_message_systeme(memory_filter):
    memory_filter._search = lambda q: _async([{"text": "Léa fait du judo."}])

    body = await memory_filter.inlet(body_with({"role": "user", "content": "Que fait Léa ?"}))

    system = body["messages"][0]
    assert system["role"] == "system"
    assert "Léa fait du judo." in system["content"]


async def test_inlet_complete_le_message_systeme_existant_sans_l_ecraser(memory_filter):
    memory_filter._search = lambda q: _async([{"text": "Léa fait du judo."}])

    body = await memory_filter.inlet(
        body_with(
            {"role": "system", "content": "Tu es Batman."},
            {"role": "user", "content": "Que fait Léa ?"},
        )
    )

    system = body["messages"][0]
    assert "Tu es Batman." in system["content"]
    assert "Léa fait du judo." in system["content"]
    assert sum(m["role"] == "system" for m in body["messages"]) == 1


async def test_inlet_fail_open_si_le_memory_forge_est_injoignable(memory_filter):
    async def broken(query):
        raise ConnectionError("memory forge down")

    memory_filter._search = broken
    original = body_with({"role": "user", "content": "Bonjour"})

    body = await memory_filter.inlet(dict(original))

    assert body["messages"] == original["messages"]


async def test_outlet_capture_le_dernier_echange(memory_filter):
    sent = []

    async def capture(content, name):
        sent.append({"content": content, "name": name})

    memory_filter._send_episode = capture

    await memory_filter.outlet(
        body_with(
            {"role": "user", "content": "Léa commence le judo."},
            {"role": "assistant", "content": "C'est noté !"},
        )
    )

    assert len(sent) == 1
    assert "Léa commence le judo." in sent[0]["content"]
    assert "C'est noté !" in sent[0]["content"]
    assert "chat-42" in sent[0]["name"]


async def test_outlet_n_echoue_jamais_meme_si_l_envoi_echoue(memory_filter):
    async def broken(content, name):
        raise ConnectionError("memory forge down")

    memory_filter._send_episode = broken
    body = body_with(
        {"role": "user", "content": "Bonjour"}, {"role": "assistant", "content": "Salut"}
    )

    assert await memory_filter.outlet(dict(body)) == body


async def test_la_valve_enabled_false_desactive_tout(memory_filter):
    calls = []
    memory_filter._search = lambda q: _async(calls.append("search"))
    memory_filter._send_episode = lambda c, n: _async(calls.append("episode"))
    memory_filter.valves.enabled = False
    body = body_with(
        {"role": "user", "content": "Bonjour"}, {"role": "assistant", "content": "Salut"}
    )

    await memory_filter.inlet(dict(body))
    await memory_filter.outlet(dict(body))

    assert calls == []


async def _async(value):
    return value
