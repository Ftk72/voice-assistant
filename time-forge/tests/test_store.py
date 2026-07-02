"""Contrat du port AgendaStore, appliqué aux deux implémentations."""

from datetime import datetime, timedelta

import pytest

from app.schemas import EventIn
from app.store.memory import InMemoryAgenda
from app.store.sqlite import SqliteAgenda


@pytest.fixture(params=["memory", "sqlite"])
def store(request, tmp_path):
    if request.param == "sqlite":
        return SqliteAgenda(tmp_path / "agenda.db")
    return InMemoryAgenda()


NOW = datetime(2026, 7, 2, 9, 0)


async def test_add_puis_list(store):
    await store.add(EventIn(title="Dentiste", when=NOW + timedelta(days=1)))
    await store.add(EventIn(title="Trop loin", when=NOW + timedelta(days=30)))

    events = await store.list_between(NOW, NOW + timedelta(days=7))

    assert [event.title for event in events] == ["Dentiste"]


async def test_list_est_trie_par_date(store):
    await store.add(EventIn(title="Après", when=NOW + timedelta(hours=5)))
    await store.add(EventIn(title="Avant", when=NOW + timedelta(hours=1)))

    events = await store.list_between(NOW, NOW + timedelta(days=1))

    assert [event.title for event in events] == ["Avant", "Après"]


async def test_delete(store):
    event = await store.add(EventIn(title="À supprimer", when=NOW))

    assert await store.delete(event.id) is True
    assert await store.delete(event.id) is False
    assert await store.list_between(NOW - timedelta(days=1), NOW + timedelta(days=1)) == []


async def test_claim_due_respecte_le_preavis(store):
    # Rappel à 10 h : dû à 10 h pile (préavis 0).
    await store.add(EventIn(title="Rappel", when=NOW + timedelta(hours=1), announce_lead_minutes=0))
    # Rendez-vous à 10 h, préavis 60 min : dû dès 9 h.
    await store.add(EventIn(title="RDV", when=NOW + timedelta(hours=1), announce_lead_minutes=60))
    # Sans préavis : jamais annoncé.
    await store.add(EventIn(title="Consultatif", when=NOW + timedelta(hours=1)))

    due_a_9h = await store.claim_due(NOW)

    assert [event.title for event in due_a_9h] == ["RDV"]

    due_a_10h = await store.claim_due(NOW + timedelta(hours=1))

    assert [event.title for event in due_a_10h] == ["Rappel"]


async def test_claim_due_n_annonce_qu_une_fois(store):
    await store.add(EventIn(title="Unique", when=NOW, announce_lead_minutes=0))

    assert len(await store.claim_due(NOW)) == 1
    assert await store.claim_due(NOW + timedelta(minutes=5)) == []


async def test_sqlite_survit_a_la_reouverture(tmp_path):
    path = tmp_path / "agenda.db"
    first = SqliteAgenda(path)
    await first.add(EventIn(title="Persistant", when=NOW + timedelta(days=1)))

    reopened = SqliteAgenda(path)
    events = await reopened.list_between(NOW, NOW + timedelta(days=7))

    assert [event.title for event in events] == ["Persistant"]
