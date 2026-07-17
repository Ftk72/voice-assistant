import functools
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

    def __init__(
        self,
        engine_factory: Callable[[], ChatterboxEngine] | None = None,
        chatterbox_dir: Path | None = None,
    ) -> None:
        self.chatterbox_dir = chatterbox_dir
        self._engine_factory = engine_factory or functools.partial(
            _RealChatterboxEngine, local_dir=chatterbox_dir
        )
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
    requis qu'à l'exécution avec VOICE_FORGE_PROVIDER=chatterbox.

    Exécuté au réel : synthèse française clonée validée à l'oreille dans la
    nouvelle stack (aperçu /admin, poste Windows, 2026-07-17) — ~1,75 s en
    régime, WAV PCM16 mono 24 kHz, sm_120 (capability 12.0) confirmé sur
    RTX 5080 via torch 2.8/cu128 (ticket wayfinder 0012).

    Deux modes, selon `local_dir` :
    - `local_dir` fourni : pipeline anglais `ChatterboxTTS` chargé via
      `from_local`, dont le `t3_cfg.safetensors` a été remplacé par le
      fine-tune français Thomcles/Chatterbox-TTS-French. Ce pipeline ne
      connaît pas la notion de langue (`generate()` n'a pas de paramètre
      `language_id`) : le paramètre `language` reçu par `synthesize_wav`
      est donc ignoré, un avertissement est loggé une seule fois au
      chargement.
    - `local_dir` absent : comportement historique, pipeline multilingue
      `ChatterboxMultilingualTTS.from_pretrained`, sélection de la langue
      via `language_id`.
    """

    def __init__(self, local_dir: Path | None = None) -> None:
        self._local_dir = local_dir
        if local_dir is not None:
            from chatterbox.tts import ChatterboxTTS

            logger.debug(
                "Chatterbox : pipeline anglais + fine-tune T3 français (%s) — "
                "paramètre 'language' ignoré (pas de language_id sur ce pipeline).",
                local_dir,
            )
            self._model = ChatterboxTTS.from_local(str(local_dir), device="cuda")
        else:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS

            self._model = ChatterboxMultilingualTTS.from_pretrained(device="cuda")

    def synthesize_wav(
        self, text: str, speaker_wav: Path, *, language: str, exaggeration: float, cfg_weight: float
    ) -> bytes:
        import io

        import torchaudio

        if self._local_dir is not None:
            wav = self._model.generate(
                text,
                audio_prompt_path=str(speaker_wav),
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
            )
        else:
            wav = self._model.generate(
                text,
                language_id=language,
                audio_prompt_path=str(speaker_wav),
                exaggeration=exaggeration,
                cfg_weight=cfg_weight,
            )
        buffer = io.BytesIO()
        # PCM 16 bits explicite : par défaut torchaudio sauve le tenseur en
        # float32 (code de format WAV 3, données à l'offset 80), que les clients
        # OpenAI-compat lisent comme du PCM 16 bits → grésillement constaté au
        # premier run réel du transport voix (2026-07-10).
        torchaudio.save(
            buffer, wav, self._model.sr, format="wav", encoding="PCM_S", bits_per_sample=16
        )
        return buffer.getvalue()
