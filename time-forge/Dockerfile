FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app

ENV TIME_FORGE_HOST=0.0.0.0
EXPOSE 8400

CMD ["uv", "run", "--no-sync", "python", "-m", "app"]
