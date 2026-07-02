import json
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from app.providers.base import BaseTTSProvider

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = "fr"
DEFAULT_EXAGGERATION = 0.5
DEFAULT_CFG_WEIGHT = 0.5


class ChatterboxEngine(Protocol):
    """Couche mince au-dessus du modèle Chatterbox, injectable pour les tests."""

    def synthesize_wav(
        self, text: str, speaker_wav: Path, *, language: str, exaggeration: float, cfg_weight: float
    ) -> bytes: ...


class ChatterboxProvider(BaseTTSProvider):
    """Synthèse + clonage zero-shot via Chatterbox Multilingual (ADR 0002).

    Le modèle n'est chargé qu'à la première synthèse : le service démarre
    instantanément et sans GPU tant qu'aucune requête TTS n'arrive.
    """

    media_type = "audio/wav"

    def __init__(self, engine_factory: Callable[[], ChatterboxEngine] | None = None) -> None:
        self._engine_factory = engine_factory or _RealChatterboxEngine
        self._engine: ChatterboxEngine | None = None

    def synthesize(self, text: str, speaker_wav: Path) -> bytes:
        if self._engine is None:
            logger.info("Chargement du modèle Chatterbox…")
            self._engine = self._engine_factory()
        params = self._voice_params(speaker_wav)
        started = time.perf_counter()
        audio = self._engine.synthesize_wav(text, speaker_wav, **params)
        logger.info(
            "Synthèse voix=%s lang=%s %d car. en %.2f s",
            speaker_wav.parent.name,
            params["language"],
            len(text),
            time.perf_counter() - started,
        )
        return audio

    @staticmethod
    def _voice_params(speaker_wav: Path) -> dict:
        """Paramètres de la voix, surchargés par voices/Nom/config.json s'il existe."""
        params = {
            "language": DEFAULT_LANGUAGE,
            "exaggeration": DEFAULT_EXAGGERATION,
            "cfg_weight": DEFAULT_CFG_WEIGHT,
        }
        config_file = speaker_wav.parent / "config.json"
        if config_file.is_file():
            overrides = json.loads(config_file.read_text())
            params.update({key: overrides[key] for key in params if key in overrides})
        return params


class _RealChatterboxEngine:
    """Adaptateur du vrai modèle. Imports paresseux : chatterbox/torch ne sont
    requis qu'à l'exécution avec VOICE_FORGE_PROVIDER=chatterbox."""

    def __init__(self) -> None:
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        self._model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")

    def synthesize_wav(
        self, text: str, speaker_wav: Path, *, language: str, exaggeration: float, cfg_weight: float
    ) -> bytes:
        import io

        import torchaudio

        wav = self._model.generate(
            text,
            language_id=language,
            audio_prompt_path=str(speaker_wav),
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
        )
        buffer = io.BytesIO()
        torchaudio.save(buffer, wav, self._model.sr, format="wav")
        return buffer.getvalue()
