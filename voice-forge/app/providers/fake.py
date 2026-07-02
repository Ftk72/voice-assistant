import io
import wave
from pathlib import Path

from app.providers.base import BaseTTSProvider


class FakeProvider(BaseTTSProvider):
    """Provider de développement : un WAV silencieux, sans GPU ni modèle."""

    media_type = "audio/wav"

    def synthesize(self, text: str, speaker_wav: Path) -> bytes:
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(24_000)
            wav.writeframes(b"\x00\x00" * 2_400)  # 100 ms de silence
        return buffer.getvalue()
