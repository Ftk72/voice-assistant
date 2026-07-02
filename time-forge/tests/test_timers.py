import asyncio

from app.announce.log import LogAnnouncer
from app.timers import TimerBoard


async def test_le_minuteur_annonce_a_l_echeance_puis_disparait():
    announcer = LogAnnouncer()
    board = TimerBoard(announcer)

    board.start("pâtes", seconds=0)
    await asyncio.sleep(0.05)

    assert announcer.spoken == ["Le minuteur « pâtes » est terminé."]
    assert board.active() == []  # ne survit pas à son échéance (CONTEXT.md)


async def test_annuler_empeche_l_annonce():
    announcer = LogAnnouncer()
    board = TimerBoard(announcer)

    board.start("thé", seconds=60)
    assert board.cancel("thé") is True
    await asyncio.sleep(0.05)

    assert announcer.spoken == []
    assert board.cancel("thé") is False


async def test_relancer_un_label_remet_a_zero():
    announcer = LogAnnouncer()
    board = TimerBoard(announcer)

    board.start("pâtes", seconds=60)
    board.start("pâtes", seconds=120)

    assert len(board.active()) == 1


async def test_les_minuteurs_sont_tries_par_echeance():
    board = TimerBoard(LogAnnouncer())

    board.start("lent", seconds=300)
    board.start("rapide", seconds=30)

    assert [timer.label for timer in board.active()] == ["rapide", "lent"]
