# Handoff 0002 — Voice assistant codé ; prochaine session : Memory Forge et/ou jour de téléchargement

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent fait foi (voir `README.md` du dossier). En fin de session, générer le 0003 via `/handoff`.

Date : 2026-07-02 · Remplace le 0001. Sessions couvertes : implémentation complète des étapes 1-6 du plan v1 (sans téléchargement, connexion lente ce jour-là) + session de grilling « mémoire persistante » (14 questions, toutes résolues).

## Lire avant tout (fait autorité, ne pas redériver)

- `CONTEXT.md` — glossaire (assistant vocal + § Mémoire phase 2)
- `docs/adr/0001..0005` — décisions techniques (0005 = Graphiti/Neo4j, tout frais)
- `docs/ACCEPTANCE.md` (v1 vocal) et `docs/ACCEPTANCE-MEMOIRE.md` (phase 2)
- `README.md` racine + `voice-forge/README.md`

## État du dépôt (`/home/ftk/voice-assistant/`)

**Le voice assistant v1 est entièrement codé, jamais exécuté en réel** (aucun modèle téléchargé, Docker Desktop non intégré à cette distro WSL) :

- `voice-forge/` — FastAPI complet : contrat OpenAI (`/audio/voices`, `/audio/speech`, alias `/v1`, `/health`), VoiceManager (scan à chaud), providers (Fake / Chatterbox lazy / cache disque), mini-page d'admin `/admin`. **22 tests pytest verts sans GPU** (`uv run pytest`), ruff propre. Deps lourdes isolées : `uv sync --extra chatterbox` (torch, à faire plus tard).
- `docker-compose.yml` — 4 services (openwebui v0.10.2 / llm Qwen3.6-35B-A3B / stt Voxtral / voice-forge), YAML validé mais **jamais lancé**.
- `scripts/download-models.sh` — ~26 Go, **noms de dépôts HF écrits de mémoire, à vérifier**.
- `personas/`, `docs/OPENWEBUI.md` — prompts voice-first + config (piège PersistentConfig documenté).

Clone lecture seule d'OpenWebUI : `/home/ftk/openwebui/` (v0.10.2). Vérifié dedans : env vars audio, champ natif « TTS Voice » de l'éditeur de modèle, client MCP natif (`utils/mcp/client.py`), Filter inlet/outlet, builtin tools.

## Phase 2 décidée (grilling complet, rien codé)

Mémoire en graphe unique (souvenirs conversationnels + documents md/PDF) : Graphiti + Neo4j dans un service custom **Memory Forge** ; extraction différée sur le 35B, injection via Filter + recall/forget via MCP, bge-m3 CPU, capture totale + oubli réel + persona off-record, Neo4j Browser puis visu custom. Détails et justifications : ADR 0005 + ACCEPTANCE-MEMOIRE.md. Plan en 5 phases validé par l'utilisateur (socle → mémoire conversationnelle → recall/forget → documents → visualisation).

## Prochaines actions possibles

**Si connexion lente encore** : coder le squelette Memory Forge (phase 1) sans téléchargement — même pattern que voice-forge (FastAPI, TDD, extracteur/graphe factices derrière un seam ; `graphiti-core` lui-même est un petit paquet mais attendre pour Neo4j/bge-m3).

**Jour de bonne connexion (checklist aussi dans README racine)** :
1. Activer l'intégration Docker Desktop pour cette distro WSL ; `docker compose config` pour valider le compose.
2. Vérifier les dépôts HF dans `scripts/download-models.sh`, lancer (~26 Go).
3. `uv sync --extra chatterbox` puis **valider `_RealChatterboxEngine`** (`voice-forge/app/providers/chatterbox.py`) — écrit d'après la doc, jamais exécuté ; l'API réelle de chatterbox-tts peut différer.
4. `docker compose up -d --build`, config OpenWebUI (docs/OPENWEBUI.md), personas, **mesurer la latence ≤ 2 s** (ACCEPTANCE.md).

## Méthode de travail exigée par l'utilisateur (inchangée)

- Par étape : analyser → proposer → expliquer → **attendre validation** → coder (TDD) → tests → documentation. Jamais coder sans validation (une validation « enchaîne les N étapes » en bloc est acceptée s'il la donne).
- Zéro fork/modification d'OpenWebUI ; toujours ses mécanismes natifs ; dialecte OpenAI exact ; vérifier dans le clone plutôt que de mémoire.
- Utilisateur francophone — tout en français. Maintenir CONTEXT.md et ADR au fil de l'eau.

## Suggested skills

- `/tdd` — pour tout développement (Voice Forge l'a suivi ; Memory Forge devra aussi).
- `/grilling` ou `/grill-with-docs` — pour toute nouvelle décision d'architecture (ex. si Graphiti s'avère inadapté au 35B local).
- `/domain-modeling` — maintenir CONTEXT.md/ADR pendant le code.
- `/verify` ou `/run` — le jour du premier lancement réel de la stack.
- `/handoff` — en fin de session, générer le 0003.

Skills côté WSL : `/home/ftk/.claude/skills/` (copies, pas symlinks).
