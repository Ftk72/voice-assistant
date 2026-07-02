import hashlib
import logging
from pathlib import Path

from app.providers.base import BaseTTSProvider

logger = logging.getLogger(__name__)


class CachedProvider(BaseTTSProvider):
    """Cache disque : une même phrase avec la même voix n'est synthétisée qu'une fois."""

    def __init__(self, inner: BaseTTSProvider, cache_dir: Path) -> None:
        self.inner = inner
        self.media_type = inner.media_type
        self._cache_dir = cache_dir

    def synthesize(self, text: str, speaker_wav: Path) -> bytes:
        key = hashlib.sha256(
            f"{type(self.inner).__name__}|{speaker_wav.parent.name}|{text}".encode()
        ).hexdigest()
        cached = self._cache_dir / f"{key}.audio"
        if cached.is_file():
            logger.debug("Cache hit voix=%s", speaker_wav.parent.name)
            return cached.read_bytes()
        audio = self.inner.synthesize(text, speaker_wav)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cached.write_bytes(audio)
        return audio
