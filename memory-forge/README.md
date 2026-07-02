# Memory Forge

Mémoire persistante en graphe pour l'assistant vocal (phase 2) : souvenirs conversationnels + connaissances documentaires dans un seul graphe Graphiti/Neo4j, avec provenance et obsolescence. Décisions : `../docs/adr/0005` · scénarios juges : `../docs/ACCEPTANCE-MEMOIRE.md` · vocabulaire : `../CONTEXT.md` § Mémoire.

## Lancer (dev, sans Neo4j ni GPU)

```bash
uv sync
uv run python -m app        # http://127.0.0.1:8200 — backend factice
```

Configuration par variables d'environnement (préfixe `MEMORY_FORGE_`) : `BACKEND` (`fake` par défaut, `graphiti` en production — nécessite `uv sync --extra graphiti`), `NEO4J_URI`/`NEO4J_USER`/`NEO4J_PASSWORD`, `LLM_BASE_URL` (extraction différée sur le Qwen), `EMBEDDER_BASE_URL` (bge-m3), `DOCUMENTS_DIR` (ingestion documentaire, désactivée si absent), `DOCUMENTS_POLL_SECONDS` (défaut `10`), `HOST` (défaut `127.0.0.1`), `PORT` (défaut `8200`).

## API (phase 1)

- `POST /episodes` `{content, source: conversation|document, name}` → **202** immédiat, extraction en file différée (jamais pendant une conversation vocale).
- `GET /search?q=…` → `{facts: [{text, provenance, valid_at, invalid_at}]}` — consommé par la Filter OpenWebUI (injection).
- `DELETE /facts?entity=…` → oubli réel (suppression, pas invalidation).
- `GET /graph?entity=…&depth=1..3` → voisinage navigable `{center, nodes, edges}` — consommé par la page `/viz`.
- `GET /viz` — mini-page de visualisation du graphe.
- `GET /health` — healthcheck Docker.

## Architecture

`app/graph/base.py` définit le port `GraphMemory` (`add_episode`, `search`, `forget`), calqué sur les scénarios d'acceptation et non sur l'API Graphiti — l'implémentation est interchangeable sans toucher à la Filter ni au MCP.

- `InMemoryGraph` — factice (une phrase = un fait, recherche par mots) : tests et dev.
- `GraphitiMemory` — adaptateur réel. ⚠️ **Jamais exécuté** (écrit hors connexion) : à valider au premier lancement avec `uv sync --extra graphiti` + Neo4j.

## Ingestion documentaire (phase 4, ADR 0006)

Déposer un `.md` ou un `.pdf` dans `../documents/` (monté dans le conteneur) : le watcher (polling mtime, ~10 s) le découpe — markdown par sections, PDF par page — et met les épisodes dans la même file d'extraction différée que les conversations. État du watcher : `documents/.memory-forge-state.json` (le supprimer force une ré-ingestion complète). Fichier modifié → ré-ingestion naïve, les contradictions reviennent au moteur du graphe.

## Visualisation (phase 5)

http://127.0.0.1:8200/viz — recherche d'entité, extension du voisinage au clic (profondeur 1-3), filtres provenance (souvenir/document) et validité (actifs/obsolètes, arêtes pointillées), panneau des faits datés avec provenance. Page autonome (HTML/JS vanilla servie par l'app, zéro CDN — contrainte 100 % local). Neo4j Browser reste disponible pour l'exploration Cypher brute : http://127.0.0.1:7474.

⚠️ Conçue sur le backend factice : le réglage fin (layout, seuils) se fera sur graphe Graphiti peuplé, comme convenu au handoff 0003.

## Tests

```bash
uv run pytest    # sans réseau ni GPU
uv run ruff check .
```
