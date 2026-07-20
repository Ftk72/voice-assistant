FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --extra docker

COPY app ./app

ENV ACTION_FORGE_HOST=0.0.0.0
EXPOSE 8800

CMD ["uv", "run", "--no-sync", "python", "-m", "app"]
