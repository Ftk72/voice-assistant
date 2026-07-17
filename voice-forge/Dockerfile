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

# ffmpeg APRÈS le uv sync lourd : couche indépendante et légère, pour ne jamais
# invalider le cache chatterbox (~2,5 Go, ~20 min). Décode les échantillons de
# voix mp3/m4a/ogg/flac → WAV (DecodeurFfmpeg, VOICE_FORGE_DECODEUR=ffmpeg) ;
# binaire CPU, aucun enjeu sm_120.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY app ./app

ENV VOICE_FORGE_HOST=0.0.0.0
EXPOSE 8100

CMD ["uv", "run", "--no-sync", "python", "-m", "app"]
