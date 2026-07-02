from datetime import datetime, timedelta

from app.announce.log import LogAnnouncer
from app.main import announcement_text
from app.schemas import EventIn
from app.store.memory import InMemoryAgenda


def test_texte_d_annonce_rappel_vs_preavis():
    assert announcement_text("Appeler le plombier", 0) == "Rappel : Appeler le plombier."
    assert announcement_text("Dentiste", 60) == "Dans 60 minutes : Dentiste."


async def test_un_tour_de_boucle_annonce_les_dus():
    """Le cœur de la boucle sans l'attente : claim_due → announce."""
    store = InMemoryAgenda()
    announcer = LogAnnouncer()
    now = datetime(2026, 7, 2, 9, 0)
    await store.add(EventIn(title="Réunion", when=now, announce_lead_minutes=0))
    await store.add(EventIn(title="Plus tard", when=now + timedelta(hours=2),
                            announce_lead_minutes=0))

    for event in await store.claim_due(now):
        await announcer.announce(announcement_text(event.title, event.announce_lead_minutes))

    assert announcer.spoken == ["Rappel : Réunion."]
