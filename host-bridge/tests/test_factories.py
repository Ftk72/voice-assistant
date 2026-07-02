from app.actions.fake import FakeRunner
from app.actions.subprocess_runner import SubprocessRunner
from app.audio.fake import FakePlayer
from app.audio.system import SystemPlayer
from app.config import Settings
from app.main import build_player, build_runner


def test_fake_par_defaut():
    settings = Settings()

    assert isinstance(build_runner(settings), FakeRunner)
    assert isinstance(build_player(settings), FakePlayer)


def test_reels_sur_demande():
    assert isinstance(build_runner(Settings(runner="subprocess")), SubprocessRunner)
    assert isinstance(build_player(Settings(player="auto")), SystemPlayer)
