# Handoff 0004 — Memory Forge phases 4-5 codées ; prochaine étape : lancement réel

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent fait foi. En fin de session, générer le 0005 via `/handoff`.

Date : 2026-07-02 · Remplace le 0003. Session couverte : phases 4 (ingestion documentaire) et 5 (visualisation, socle) du Memory Forge — toujours **sans téléchargement de modèles** ; seul micro-paquet ajouté : `pypdf` (pur Python).

## Lire avant tout (fait autorité)

- `CONTEXT.md` (glossaire, § Mémoire) · `docs/adr/0001..0006` · `docs/ACCEPTANCE.md` + `docs/ACCEPTANCE-MEMOIRE.md`
- `README.md` racine (mis à jour : section Memory Forge ajoutée) · `voice-forge/README.md` · `memory-forge/README.md`
- Clone lecture seule OpenWebUI v0.10.2 : `/home/ftk/openwebui/` — toujours vérifier dedans plutôt que de mémoire.

## État du dépôt

**Voice assistant v1 (inchangé)** : codé, jamais exécuté en réel ; `_RealChatterboxEngine` à valider.

**Memory Forge — les 5 phases sont codées**, `memory-forge/` : **28 tests verts** (`uv run pytest`), ruff propre, `docker compose config` OK. Phases 1-3 : voir handoff 0003 (inchangées). Cette session :

- **Phase 4 (ingestion documentaire)** ✅ — ADR 0006. Dossier `documents/` racine monté dans le service `memory` (rw). `app/ingest/chunker.py` (markdown par sections `fichier.md § Titre`, PDF par page `fichier.pdf p.N` via pypdf) ; `app/ingest/watcher.py` (polling mtime, défaut 10 s, état `documents/.memory-forge-state.json` — le supprimer force la ré-ingestion) ; boucle `watch_documents` dans le lifespan, épisodes dans la même file d'extraction différée. Activation par `MEMORY_FORGE_DOCUMENTS_DIR` (compose : `/documents`). Smoke-testé en réel (backend factice) : dépôt d'un .md après démarrage → fait retrouvé via `/search`.
- **Phase 5 (visualisation, socle)** ✅ — port étendu : `GraphMemory.neighborhood(entity, depth)` → `GraphNeighborhood{center, nodes, edges}` ; endpoint `GET /graph?entity=&depth=1..3` ; page `GET /viz` (`app/viz/index.html`, HTML/JS vanilla autonome, zéro CDN) : recherche d'entité, extension au clic, filtres provenance/validité (obsolètes en pointillés), panneau des faits datés. Smoke-testé : le croisement souvenir↔document via l'entité partagée fonctionne sur le factice. **Réglage fin UX à faire sur graphe Graphiti peuplé** (choix acté au 0003). `GraphitiMemory.neighborhood` écrit en Cypher (extension par frontière, provenance parsée du `source_description`) — **jamais exécuté**, comme tout l'adaptateur.
- **Divers** : `.gitignore` racine créé, tous les `__pycache__/*.pyc` dé-trackés (`git rm --cached` **stagé, non commité** — rien n'est commité, l'utilisateur commite lui-même). Off-record vérifié : couvert par la doc (`docs/OPENWEBUI.md`) et le test de la valve `enabled`.

Le factice extrait les « entités » naïvement (mots capitalisés hors stop-words) — assumé, sert uniquement au dev de la page.

## Reprendre ici : jour de bonne connexion

**Point bloquant découvert en session : le script de téléchargement échoue.** `hf download unsloth/Qwen3.6-35B-A3B-GGUF "Qwen3.6-35B-A3B-Q4_K_M.gguf"` → *File not found in repository* (le nom de fichier a changé dans le dépôt HF). Avant de relancer `./scripts/download-models.sh`, lister les vrais noms de chaque dépôt (quelques Ko : `hf download <repo> --include "*.gguf" --dry-run`, ou l'API HF) et corriger le script — vérifier les 4 dépôts (Qwen unsloth, Voxtral ggml-org, Chatterbox ResembleAI, bge-m3 gpustack). Noter aussi : l'extra `[cli]` de huggingface_hub émet un warning (extra disparu en v1.x) — bénin.

Checklist ensuite (détail au README racine § « Reste à faire ») :

1. Intégration Docker Desktop → distro WSL ; `docker compose pull` puis `build` (torch ~2,5 Go dans l'image voice-forge).
2. `voice-forge` : valider `_RealChatterboxEngine` (`uv sync --extra chatterbox`).
3. `memory-forge` : valider `GraphitiMemory` (`uv sync --extra graphiti`) — `add_episode`/`search`/Cypher du `forget` **et le nouveau `neighborhood`** (noms de labels/propriétés `Entity`, `RELATES_TO`, `r.episodes`, `ep.source_description` à vérifier contre le vrai schéma Graphiti). Vérifier que le 35B produit du JSON structuré acceptable pour l'extraction — **risque identifié au grilling ; si la qualité déçoit, re-grillinger le choix du moteur** (le port `GraphMemory` isole le swap).
4. `docker compose up -d --build` ; config OpenWebUI (`docs/OPENWEBUI.md`) : audio, personas, Filter mémoire, MCP `http://memory:8200/mcp`.
5. Scénarios d'acceptation : latence ≤ 2 s, injection ≤ 300 ms, scénario Léa, croisement document (déposer un .md dans `documents/`), oubli, visualisation sur `http://127.0.0.1:8200/viz` — puis régler l'UX de la page sur le graphe peuplé.

## Méthode de travail exigée (inchangée)

Analyser → proposer → **attendre validation** → coder en TDD → tests → doc. Zéro fork OpenWebUI ; dialecte OpenAI/MCP exact ; tout en français ; CONTEXT.md/ADR au fil de l'eau. Ne pas lancer de gros téléchargements sans accord explicite (connexion lente) ; les requêtes API légères (HF, quelques Ko) ont été acceptées sur demande.

## Suggested skills

- `/verify` ou `/run` — premier lancement réel de la stack (l'étape qui reste).
- `/tdd` — pour toute suite de code (appliqué sur les 5 phases).
- `/grilling` — si l'extraction Graphiti/35B déçoit, ou pour le réglage UX de la visualisation sur graphe peuplé.
- `/handoff` — générer le 0005 en fin de session.
