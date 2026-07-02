from app.announce.hostbridge import HostBridgeAnnouncer
from app.announce.log import LogAnnouncer
from app.config import Settings
from app.main import build_announcer, build_store
from app.store.memory import InMemoryAgenda
from app.store.sqlite import SqliteAgenda


def test_memoire_et_log_par_defaut():
    settings = Settings()

    assert isinstance(build_store(settings), InMemoryAgenda)
    assert isinstance(build_announcer(settings), LogAnnouncer)


def test_sqlite_et_hostbridge_sur_demande(tmp_path):
    settings = Settings(
        store="sqlite", sqlite_path=tmp_path / "agenda.db", announcer="hostbridge"
    )

    assert isinstance(build_store(settings), SqliteAgenda)
    assert isinstance(build_announcer(settings), HostBridgeAnnouncer)
