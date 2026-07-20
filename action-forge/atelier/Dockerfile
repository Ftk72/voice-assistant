# L'Atelier : bac à sable jetable où les Actions (CodeAct) s'exécutent — image
# fixe (contrat 0031), sans dépôt ni secret ni socket Docker à l'intérieur.
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.11.26 /uv /uvx /bin/

RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /echange

CMD ["sleep", "infinity"]
