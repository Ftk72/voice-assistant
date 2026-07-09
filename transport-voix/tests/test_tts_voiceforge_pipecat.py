"""Sous-classe TTS Pipecat pour voice-forge (`ServiceTTSVoiceForge`).

Ces tests ne s'exécutent que si l'extra `pipecat` est installé ; sinon ils
sont sautés (le reste du composant reste vert sans l'extra).
"""

import io
import wave

import pytest

pytest.importorskip("pipecat")

from app.transport.tts_voiceforge import ServiceTTSVoiceForge  # noqa: E402

RATE = 24000


def _wav(pcm: bytes, rate: int = RATE) -> bytes:
    """Emballe du PCM 16 bits mono dans un conteneur WAV (comme voice-forge)."""
    tampon = io.BytesIO()
    with wave.open(tampon, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(pcm)
    return tampon.getvalue()


class _FauxFluxReponse:
    """Imite la réponse streaming du client OpenAI (contexte async + iter_bytes)."""

    def __init__(self, corps: bytes, status_code: int = 200) -> None:
        self._corps = corps
        self.status_code = status_code

    async def __aenter__(self) -> "_FauxFluxReponse":
        return self

    async def __aexit__(self, *_exc: object) -> bool:
        return False

    async def text(self) -> str:
        return self._corps.decode(errors="replace")

    async def iter_bytes(self, taille: int):
        for i in range(0, len(self._corps), taille):
            yield self._corps[i : i + taille]


def _brancher_faux_client(service: ServiceTTSVoiceForge, corps: bytes, status_code: int = 200):
    """Remplace `service._client.audio.speech.with_streaming_response.create`.

    Renvoie la liste `appels` où sont capturés les kwargs de chaque appel."""
    appels: list[dict] = []

    def create(**kwargs):
        appels.append(kwargs)
        return _FauxFluxReponse(corps, status_code)

    class _Espace:
        pass

    client = _Espace()
    client.audio = _Espace()
    client.audio.speech = _Espace()
    client.audio.speech.with_streaming_response = _Espace()
    client.audio.speech.with_streaming_response.create = create
    service._client = client
    service._sample_rate = RATE  # simule un service démarré (start() non appelé)
    return appels


async def _collecter(agen) -> list:
    return [frame async for frame in agen]


async def test_voix_hors_enum_openai_acceptee_et_wav_decode():
    from pipecat.frames.frames import ErrorFrame, TTSAudioRawFrame

    service = ServiceTTSVoiceForge(
        api_key="sk-local",
        base_url="http://voice-forge",
        settings=ServiceTTSVoiceForge.Settings(voice="VoixDeTest", model="voiceforge"),
        sample_rate=RATE,
    )
    pcm = b"\x01\x00\x02\x00\x03\x00\x04\x00" * 100
    appels = _brancher_faux_client(service, _wav(pcm))

    frames = await _collecter(service.run_tts("Bonjour.", "ctx-1"))

    # La voix « VoixDeTest » est passée telle quelle : aucun rejet client.
    assert not any(isinstance(f, ErrorFrame) for f in frames)
    assert appels[0]["voice"] == "VoixDeTest"
    assert "response_format" not in appels[0]  # on n'impose pas le PCM

    # L'en-tête WAV est retiré : le PCM reconstitué est exactement l'entrée.
    audio = b"".join(f.audio for f in frames if isinstance(f, TTSAudioRawFrame))
    assert audio == pcm
    assert all(
        f.sample_rate == RATE for f in frames if isinstance(f, TTSAudioRawFrame)
    )


async def test_statut_non_200_emet_une_error_frame():
    from pipecat.frames.frames import ErrorFrame

    service = ServiceTTSVoiceForge(
        api_key="sk-local",
        base_url="http://voice-forge",
        settings=ServiceTTSVoiceForge.Settings(voice="VoixDeTest", model="voiceforge"),
        sample_rate=RATE,
    )
    _brancher_faux_client(service, b"voix inconnue", status_code=400)

    frames = await _collecter(service.run_tts("Bonjour.", "ctx-1"))

    assert len(frames) == 1
    assert isinstance(frames[0], ErrorFrame)
