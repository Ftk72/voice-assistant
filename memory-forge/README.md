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
- `GET /graph/complet?limite=500&provenance=conversation|document` → le graphe entier, enrichi `{noeuds: [{nom, communaute, centralite}], aretes, tronque}` — consommé par la vue 3D de `/viz` (roadmap B1). `provenance` est optionnel (filtre les arêtes, et les nœuds qu'il isole disparaissent avec elles) ; sans limite dépassée, `tronque` vaut `false`. Les faits obsolètes (`invalid_at` non nul) sont toujours inclus, marqués — jamais omis silencieusement.
- `GET /viz` — page de visualisation 3D du graphe (voir plus bas).
- `GET /viz/vendor/{fichier}` — bibliothèques JS vendorées (3d-force-graph), zéro CDN.
- `GET /health` — healthcheck Docker.

## Architecture

`app/graph/base.py` définit le port `GraphMemory` (`add_episode`, `search`, `forget`, `neighborhood`, `graphe_complet`), calqué sur les scénarios d'acceptation et non sur l'API Graphiti — l'implémentation est interchangeable sans toucher à la Filter ni au MCP.

- `InMemoryGraph` — factice (une phrase = un fait, recherche par mots) : tests et dev.
- `GraphitiMemory` — adaptateur réel. ⚠️ **Jamais exécuté** (écrit hors connexion) : à valider au premier lancement avec `uv sync --extra graphiti` + Neo4j.

## Ingestion documentaire (phase 4, ADR 0006)

Déposer un `.md` ou un `.pdf` dans `../documents/` (monté dans le conteneur) : le watcher (polling mtime, ~10 s) le découpe — markdown par sections, PDF par page — et met les épisodes dans la même file d'extraction différée que les conversations. État du watcher : `documents/.memory-forge-state.json` (le supprimer force une ré-ingestion complète). Fichier modifié → ré-ingestion naïve, les contradictions reviennent au moteur du graphe.

## Visualisation 3D (roadmap B1, ADR 0010 point 6)

http://127.0.0.1:8200/viz — exploration 3D type InfraNodus du graphe mémoire, via
**3d-force-graph** (three.js/WebGL) vendoré en local (`app/viz/vendor/3d-force-graph.min.js`,
~1,25 Mo — aucun CDN, souveraineté). Au chargement : vue force-directed du graphe
complet (`GET /graph/complet`), couleur = communauté (détection par propagation
d'étiquettes, `app/viz/analyse.py`), taille = centralité par degré. Commandes :

- recherche d'entité + profondeur (1-3 sauts, `GET /graph`) ; clic sur un nœud =
  déplie son voisinage dans la scène ;
- cases à cocher provenance (conversation/document) ;
- bascule faits obsolètes (`invalid_at` non nul) : estompés par défaut, ou masqués ;
- bascule 2D/3D (`numDimensions`) ;
- bouton « Oublier cette entité » sur le panneau de sélection (`DELETE /facts`,
  confirmation obligatoire — suppression réelle et irréversible).

Page autonome (HTML/JS vanilla, zéro dépendance de build). L'analyse (communautés,
centralité) est du Python pur écrit main, sans networkx ni autre dépendance.
Neo4j Browser reste disponible pour l'exploration Cypher brute : http://127.0.0.1:7474.

### Lancer la nouvelle version en local (sans toucher au conteneur Docker)

Le conteneur Docker (`voice-assistant-memory-1`, port 8200) sert encore l'ancienne
page 2D tant qu'il n'a pas été rebuild (hors périmètre de ce chantier). Pour valider
la refonte sans y toucher, lancer une instance factice sur un autre port :

```bash
MEMORY_FORGE_PORT=8201 MEMORY_FORGE_BACKEND=fake uv run python -m app
# http://127.0.0.1:8201/viz
```

⚠️ Conçue et validée sur le backend factice (peuplé via `POST /episodes`) : le
réglage fin (layout, seuils de communauté) reste à faire sur un graphe Graphiti
peuplé, comme convenu au handoff 0003. La vérification visuelle de la scène 3D
(rendu WebGL, interactions souris) n'a pas été faite ici (agent sans navigateur) —
à faire par l'utilisateur à l'URL ci-dessus.

## Tests

```bash
uv run pytest    # sans réseau ni GPU
uv run ruff check .
```
