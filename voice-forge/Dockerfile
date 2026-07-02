FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Dépendances d'abord (couche cachée tant que le lock ne change pas).
# L'extra chatterbox tire torch/torchaudio — build à faire un jour de bonne connexion.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra chatterbox

COPY app ./app

ENV VOICE_FORGE_HOST=0.0.0.0
EXPOSE 8100

CMD ["uv", "run", "--no-sync", "python", "-m", "app"]
