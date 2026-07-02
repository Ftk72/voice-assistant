from pathlib import Path

from app.providers.base import BaseTTSProvider
from app.providers.cache import CachedProvider


class CountingProvider(BaseTTSProvider):
    media_type = "audio/wav"

    def __init__(self) -> None:
        self.calls = 0

    def synthesize(self, text: str, speaker_wav: Path) -> bytes:
        self.calls += 1
        return f"audio:{text}".encode()


def test_une_meme_phrase_n_est_synthetisee_qu_une_fois(tmp_path):
    inner = CountingProvider()
    provider = CachedProvider(inner, tmp_path / "cache")
    speaker = tmp_path / "Emma" / "speaker.wav"

    first = provider.synthesize("Bonjour", speaker)
    second = provider.synthesize("Bonjour", speaker)

    assert first == second == b"audio:Bonjour"
    assert inner.calls == 1


def test_un_texte_ou_une_voix_differents_resynthetisent(tmp_path):
    inner = CountingProvider()
    provider = CachedProvider(inner, tmp_path / "cache")

    provider.synthesize("Bonjour", tmp_path / "Emma" / "speaker.wav")
    provider.synthesize("Bonsoir", tmp_path / "Emma" / "speaker.wav")
    provider.synthesize("Bonjour", tmp_path / "Batman" / "speaker.wav")

    assert inner.calls == 3
