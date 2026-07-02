# Memory Forge

Mémoire persistante en graphe pour l'assistant vocal (phase 2) : souvenirs conversationnels + connaissances documentaires dans un seul graphe Graphiti/Neo4j, avec provenance et obsolescence. Décisions : `../docs/adr/0005` · scénarios juges : `../docs/ACCEPTANCE-MEMOIRE.md` · vocabulaire : `../CONTEXT.md` § Mémoire.

## Lancer (dev, sans Neo4j ni GPU)

```bash
uv sync
uv run python -m app        # http://127.0.0.1:8200 — backend factice
```

Configuration par variables d'environnement (préfixe `MEMORY_FORGE_`) : `BACKEND` (`fake` par défaut, `graphiti` en production — nécessite `uv sync --extra graphiti`), `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`, `LLM_BASE_URL` (extraction différée sur le Qwen), `EMBEDDER_BASE_URL` (bge-m3), `HOST` (défaut `127.0.0.1`), `PORT` (défaut `8200`).

## API (phase 1)

- `POST /episodes` `{content, source: conversation|document, name}` → **202** immédiat, extraction en file différée (jamais pendant une conversation vocale).
- `GET /search?q=…` → `{facts: [{text, provenance, valid_at, invalid_at}]}` — consommé par la Filter OpenWebUI (injection).
- `DELETE /facts?entity=…` → oubli réel (suppression, pas invalidation).
- `GET /health` — healthcheck Docker.

## Architecture

`app/graph/base.py` définit le port `GraphMemory` (`add_episode`, `search`, `forget`), calqué sur les scénarios d'acceptation et non sur l'API Graphiti — l'implémentation est interchangeable sans toucher à la Filter ni au MCP.

- `InMemoryGraph` — factice (une phrase = un fait, recherche par mots) : tests et dev.
- `GraphitiMemory` — adaptateur réel. ⚠️ **Jamais exécuté** (écrit hors connexion) : à valider au premier lancement avec `uv sync --extra graphiti` + Neo4j.

## À venir (phases 2-5 du plan validé)

Filter OpenWebUI (injection/capture) · endpoint MCP recall/forget + persona off-record · ingestion `documents/` (markdown + PDF) · mini-page de visualisation navigable (Neo4j Browser en attendant : http://127.0.0.1:7474).

## Tests

```bash
uv run pytest    # 7 tests, sans réseau ni GPU
uv run ruff check .
```
