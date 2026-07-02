from app.config import Settings
from app.main import build_world
from app.world.fake import FakeWorld
from app.world.real import RealWorld


def test_fake_par_defaut():
    assert isinstance(build_world(Settings()), FakeWorld)


def test_real_sur_demande():
    world = build_world(Settings(gateway="real"))

    assert isinstance(world, RealWorld)
