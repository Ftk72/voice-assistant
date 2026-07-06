from app.config import Settings
from app.providers.chatterbox import ChatterboxProvider
from app.providers.factory import build_provider
from app.providers.fake import FakeProvider


def test_le_provider_par_defaut_est_fake():
    provider = build_provider(Settings())

    assert isinstance(provider, FakeProvider)


def test_chatterbox_est_selectionnable_sans_charger_le_modele(tmp_path):
    provider = build_provider(Settings(provider="chatterbox", cache_dir=tmp_path / "cache"))

    # La construction ne doit ni importer chatterbox ni toucher le GPU.
    assert isinstance(provider.inner, ChatterboxProvider)


def test_chatterbox_recoit_le_repertoire_local_des_settings(tmp_path):
    chatterbox_dir = tmp_path / "modele"
    provider = build_provider(Settings(provider="chatterbox", chatterbox_dir=chatterbox_dir))

    assert provider.chatterbox_dir == chatterbox_dir


def test_le_cache_enveloppe_le_provider_si_cache_dir(tmp_path):
    from app.providers.cache import CachedProvider

    provider = build_provider(Settings(provider="fake", cache_dir=tmp_path / "cache"))

    assert isinstance(provider, CachedProvider)
    assert isinstance(provider.inner, FakeProvider)
