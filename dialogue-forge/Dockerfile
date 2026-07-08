FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY app ./app

ENV DIALOGUE_FORGE_HOST=0.0.0.0
EXPOSE 8600

CMD ["uv", "run", "--no-sync", "python", "-m", "app"]
