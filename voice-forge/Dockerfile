FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel

COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /uvx /bin/

WORKDIR /app

# Dépendances d'abord (couche cachée tant que le lock ne change pas).
# Les extras tirent torch/torchaudio — build à faire un jour de bonne connexion.
# TTS_EXTRA choisit le moteur embarqué : chatterbox (défaut) ou qwen3tts —
# les deux extras sont conflictuels (épinglages transformers incompatibles),
# une image n'en contient qu'un. Ex. : docker compose build voice-forge
# --build-arg TTS_EXTRA=qwen3tts
ARG TTS_EXTRA=chatterbox
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra "${TTS_EXTRA}"

COPY app ./app

ENV VOICE_FORGE_HOST=0.0.0.0
EXPOSE 8100

CMD ["uv", "run", "--no-sync", "python", "-m", "app"]
