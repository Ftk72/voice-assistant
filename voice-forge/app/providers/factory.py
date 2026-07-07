from app.config import Settings
from app.providers.base import BaseTTSProvider
from app.providers.cache import CachedProvider
from app.providers.chatterbox import ChatterboxProvider
from app.providers.fake import FakeProvider
from app.providers.qwen3tts import Qwen3TTSProvider


def build_provider(settings: Settings) -> BaseTTSProvider:
    provider: BaseTTSProvider
    if settings.provider == "chatterbox":
        provider = ChatterboxProvider(chatterbox_dir=settings.chatterbox_dir)
    elif settings.provider == "qwen3tts":
        provider = Qwen3TTSProvider(model_dir=settings.qwen3tts_dir)
    else:
        provider = FakeProvider()
    if settings.cache_dir is not None:
        provider = CachedProvider(provider, settings.cache_dir)
    return provider
