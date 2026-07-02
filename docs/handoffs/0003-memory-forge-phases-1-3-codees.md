# Handoff 0003 — Memory Forge phases 1-3 codées ; reprendre à la phase 4 (documents)

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent fait foi. En fin de session, générer le 0004 via `/handoff`.

Date : 2026-07-02 · Remplace le 0002. Session couverte : implémentation des phases 1-3 du Memory Forge (toujours **sans téléchargement de modèles** — connexion lente ; seuls des micro-paquets pip purs Python ont été ajoutés : `mcp`, httpx2…).

## Lire avant tout (fait autorité)

- `CONTEXT.md` (glossaire, § Mémoire) · `docs/adr/0001..0005` · `docs/ACCEPTANCE.md` + `docs/ACCEPTANCE-MEMOIRE.md`
- `README.md` racine · `voice-forge/README.md` · `memory-forge/README.md`
- Clone lecture seule OpenWebUI v0.10.2 : `/home/ftk/openwebui/` — toujours vérifier dedans plutôt que de mémoire.

## État du dépôt

**Voice assistant v1 (inchangé depuis 0002)** : entièrement codé, jamais exécuté en réel. `voice-forge/` 22 tests verts ; compose 4 services ; personas ; `_RealChatterboxEngine` non exécuté ; dépôts HF du script à vérifier.

**Memory Forge (nouveau)** — `memory-forge/`, **17 tests verts** (`uv run pytest`), ruff propre, smoke-testé en réel avec le backend factice :

- **Phase 1 (socle)** ✅ : port `GraphMemory` (`add_episode`/`search`/`forget`, calqué sur ACCEPTANCE-MEMOIRE, pas sur Graphiti) ; `InMemoryGraph` factice ; **`GraphitiMemory` écrit mais jamais exécuté** (`app/graph/graphiti.py`, erreur explicite sans `uv sync --extra graphiti`) ; API REST (`POST /episodes` → 202 + file asyncio, `GET /search`, `DELETE /facts`, `/health`) ; Dockerfile ; compose étendu (services `neo4j` avec Browser sur 127.0.0.1:7474, `embedder` bge-m3 CPU, `memory` port 8200) ; bge-m3 ajouté à `scripts/download-models.sh` (dépôt HF à vérifier).
- **Phase 2 (Filter)** ✅ : `openwebui/functions/memory_filter.py` — inlet = injection de faits en message système (fusion sans écraser le prompt persona), outlet = capture de l'échange, fail-open 300 ms, valves. Testée dans la suite memory-forge (signatures vérifiées dans `utils/filter.py` du clone). Installation documentée dans `docs/OPENWEBUI.md`.
- **Phase 3 (MCP)** ✅ : `app/mcp_server.py` — outils `recall` (faits datés + provenance + statut) et `forget` (suppression réelle, description imposant l'annonce préalable), FastMCP stateless monté sur `/mcp` dans la même app. Branchement documenté dans `docs/OPENWEBUI.md`.

## Reprendre ici : phase 4 — ingestion documentaire

Proposition faite, **non validée** (session close à ce moment) : dossier `documents/` (pattern voices/), watcher par polling mtime (~10 s, fiable sur bind-mounts WSL), découpage markdown par sections / PDF par page (`pypdf`, ~2 Mo), état `.memory-forge-state.json`, ré-ingestion naïve confiée à la résolution de contradictions de Graphiti. **Re-proposer et attendre validation** (l'utilisateur a choisi la validation phase par phase pour le Memory Forge).

Ensuite : **phase 5** — mini-page de visualisation navigable (recherche d'entité, voisinage, filtres provenance/validité), à concevoir sur graphe peuplé ; Neo4j Browser en attendant.

## Jour de bonne connexion (checklist complète au README racine)

1. Intégration Docker Desktop → cette distro WSL ; `docker compose config`.
2. Vérifier les dépôts HF dans `scripts/download-models.sh` (Qwen3.6, Voxtral, Chatterbox, bge-m3) ; lancer (~27 Go).
3. `voice-forge` : `uv sync --extra chatterbox` ; **valider `_RealChatterboxEngine`**.
4. `memory-forge` : `uv sync --extra graphiti` ; **valider `GraphitiMemory`** (API écrite d'après la doc : constructeur `Graphiti(uri, user, password, llm_client=OpenAIGenericClient, embedder=OpenAIEmbedder)`, `add_episode`, `search`, Cypher du forget) ; vérifier que le 35B produit du JSON structuré acceptable pour l'extraction Graphiti — **risque identifié au grilling ; si la qualité déçoit, re-grillinger le choix du moteur** (le port `GraphMemory` isole le swap).
5. `docker compose up -d --build` ; config OpenWebUI (`docs/OPENWEBUI.md`) : audio, personas, Filter mémoire, serveur MCP `http://memory:8200/mcp`.
6. Mesurer : latence vocale ≤ 2 s (ACCEPTANCE.md) et surcoût injection ≤ 300 ms (ACCEPTANCE-MEMOIRE.md).

## Méthode de travail exigée (inchangée)

Analyser → proposer → **attendre validation** → coder en TDD → tests → doc. Pour le Memory Forge : validation **phase par phase** (choix explicite de l'utilisateur). Zéro fork OpenWebUI ; dialecte OpenAI/MCP exact ; tout en français ; CONTEXT.md/ADR au fil de l'eau.

## Suggested skills

- `/tdd` — développement (appliqué partout jusqu'ici).
- `/grilling` — si l'extraction Graphiti/35B déçoit ou pour toute nouvelle décision d'architecture.
- `/domain-modeling` — CONTEXT.md/ADR.
- `/verify` ou `/run` — premier lancement réel de la stack.
- `/handoff` — générer le 0004 en fin de session.
