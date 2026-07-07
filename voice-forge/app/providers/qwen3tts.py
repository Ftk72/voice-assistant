import functools
import json
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from app.providers.base import BaseTTSProvider

logger = logging.getLogger(__name__)

# Qwen3-TTS attend le nom anglais de la langue (« French »), pas un code ISO.
DEFAULT_LANGUAGE = "French"


class Qwen3TTSEngine(Protocol):
    """Couche mince au-dessus du modèle Qwen3-TTS, injectable pour les tests."""

    def synthesize_wav(
        self, text: str, speaker_wav: Path, *, language: str, ref_text: str | None
    ) -> bytes: ...


class Qwen3TTSProvider(BaseTTSProvider):
    """Synthèse + clonage 3 s via Qwen3-TTS Base (candidat successeur de
    Chatterbox : premier son ~100 ms en streaming, cible latence ≤ 2 s).

    Le modèle n'est chargé qu'à la première synthèse : le service démarre
    instantanément et sans GPU tant qu'aucune requête TTS n'arrive.
    """

    media_type = "audio/wav"

    def __init__(
        self,
        engine_factory: Callable[[], Qwen3TTSEngine] | None = None,
        model_dir: Path | None = None,
    ) -> None:
        self.model_dir = model_dir
        self._engine_factory = engine_factory or functools.partial(
            _RealQwen3TTSEngine, model_dir=model_dir
        )
        self._engine: Qwen3TTSEngine | None = None

    def synthesize(self, text: str, speaker_wav: Path) -> bytes:
        if self._engine is None:
            logger.info("Chargement du modèle Qwen3-TTS…")
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
        """Paramètres de la voix, surchargés par voices/Nom/config.json s'il existe.

        `ref_text` = transcription exacte de l'échantillon speaker.wav : sans
        elle, le clonage passe en mode x-vector seul (qualité moindre d'après
        l'amont) — la fournir dans le config.json de la voix dès que possible.
        """
        params = {"language": DEFAULT_LANGUAGE, "ref_text": None}
        config_file = speaker_wav.parent / "config.json"
        if config_file.is_file():
            overrides = json.loads(config_file.read_text())
            params.update({key: overrides[key] for key in params if key in overrides})
        return params


class _RealQwen3TTSEngine:
    """Adaptateur du vrai modèle. Imports paresseux : qwen_tts/torch ne sont
    requis qu'à l'exécution avec VOICE_FORGE_PROVIDER=qwen3tts
    (extra `uv sync --extra qwen3tts`).

    Jamais exécuté à ce jour.

    Le prompt de clonage (x-vector ou audio+transcript) est mis en cache par
    chemin d'échantillon : il n'est calculé qu'à la première synthèse de
    chaque voix. Incertitude assumée jusqu'à la première exécution réelle :
    le paquet qwen-tts peut vouloir télécharger le tokenizer audio
    Qwen3-TTS-Tokenizer-12Hz depuis HF s'il ne le trouve pas — les poids
    sont déjà dans models/qwen3-tts/tokenizer, à raccorder au besoin.
    """

    def __init__(self, model_dir: Path | None = None) -> None:
        import torch
        from qwen_tts import Qwen3TTSModel

        if model_dir is None:
            raise ValueError(
                "VOICE_FORGE_QWEN3TTS_DIR est requis avec le provider qwen3tts "
                "(chemin local des poids — aucun téléchargement à l'exécution)."
            )
        self._model = Qwen3TTSModel.from_pretrained(
            str(model_dir),
            device_map="cuda:0",
            dtype=torch.bfloat16,
        )
        self._prompts: dict[Path, object] = {}

    def synthesize_wav(
        self, text: str, speaker_wav: Path, *, language: str, ref_text: str | None
    ) -> bytes:
        import io

        import soundfile

        prompt = self._prompts.get(speaker_wav)
        if prompt is None:
            prompt = self._model.create_voice_clone_prompt(
                ref_audio=str(speaker_wav),
                ref_text=ref_text,
                x_vector_only_mode=ref_text is None,
            )
            self._prompts[speaker_wav] = prompt
        wavs, sample_rate = self._model.generate_voice_clone(
            text=text,
            language=language,
            voice_clone_prompt=prompt,
        )
        buffer = io.BytesIO()
        soundfile.write(buffer, wavs[0], sample_rate, format="WAV")
        return buffer.getvalue()
