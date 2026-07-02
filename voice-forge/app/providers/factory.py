from app.config import Settings
from app.providers.base import BaseTTSProvider
from app.providers.cache import CachedProvider
from app.providers.chatterbox import ChatterboxProvider
from app.providers.fake import FakeProvider


def build_provider(settings: Settings) -> BaseTTSProvider:
    provider: BaseTTSProvider = (
        ChatterboxProvider() if settings.provider == "chatterbox" else FakeProvider()
    )
    if settings.cache_dir is not None:
        provider = CachedProvider(provider, settings.cache_dir)
    return provider
