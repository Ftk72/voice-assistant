# Handoff 0007 — Stack lançable : 4 modèles en place, dépendances et images figées ; prochaine étape : premier build + lancement réel

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent fait foi. En fin de session, générer le 0008 via `/handoff`.

Date : 2026-07-06 · Remplace le 0006. Session couverte : mise en place des 4 modèles, branchement du Chatterbox français dans voice-forge, réparation du build (numba/llvmlite), gel de toutes les images Docker. **Tout est commité par l'utilisateur** — commit `00c6717` « Stack lançable : Chatterbox FR, compatibilité dépendances et images figées » ; arbre propre.

## Lire avant tout (fait autorité)

- `CLAUDE.md` · `CONTEXT.md` · `docs/adr/0001..0008` · `docs/ACCEPTANCE*.md`
- **`docs/impasses.md`** — registre du savoir négatif ; à consulter avant tout diagnostic. Deux entrées : HF (périmée) et **la nouvelle du 2026-07-06** (bornage `requires-python` insuffisant — voir « Reprendre ici » point 1).
- Le commit `00c6717` porte tout le diff de cette session : ne pas le redécrire, le lire (`git show 00c6717`).
- Clone lecture seule OpenWebUI v0.10.2 : `/home/ftk/openwebui/`.

## État du dépôt et de l'environnement

**Les 4 emplacements de modèles sont complets** (`models/`, dossier ignoré par git) :
- `llm/qwen3.6-35b-a3b-q4_k_m.gguf` (20 Go) — variante Uncensored choisie par l'utilisateur (cf. 0006).
- `stt/voxtral-mini-q4_k_m.gguf` + `voxtral-mini-mmproj.gguf` (3 Go) — téléchargés manuellement par l'utilisateur cette session.
- `chatterbox/` (3 Go) — 5 fichiers : `t3_cfg.safetensors` **français** (Thomcles) + `ve/s3gen.safetensors`, `tokenizer.json`, `conds.pt` (base ResembleAI).
- `embedder/bge-m3-q8_0.gguf` (606 Mo).
- Reste `models/voxtral-tts-q4.gguf` à la racine : **piste TTS future** (runtime Rust/C hors llama.cpp — nécessiterait un ADR), pas branchée.

**Environnement nouveau cette session** : Docker 29.5.3 accessible dans la distro WSL, GPU **RTX 5080 (16 Go, Blackwell/sm_120)** visible. **Images tirées/buildées** : openwebui, llama.cpp server-cuda + server, neo4j, searxng (pull réussis). Les 4 forges légères (world/time/memory + world) buildent ; **voice-forge NON encore rebuildé après le correctif** (le build précédent échouait, cf. impasse — désormais réparé mais à relancer).

**Code** : 5 forges vertes (voice-forge 25 tests, memory 28, world 20, time 30, host-bridge 20), ruff propre partout. Le Pont hôte a **tourné en réel** cette session (santé + jeton `X-Bridge-Token` + handshake MCP OK) — premier composant validé hors tests.

## Ce qui a changé (résumé — détail dans `git show 00c6717`)

- **Chatterbox FR branché** : `voice-forge` charge `ChatterboxTTS.from_local` via `VOICE_FORGE_CHATTERBOX_DIR=/models/chatterbox` (pipeline anglais + T3 français, `generate()` sans `language_id`). Volume monté dans le compose. Adaptateur réel toujours **jamais exécuté**.
- **Compatibilité dépendances** : `requires-python = ">=3.12,<3.13"` dans les 5 forges + `[tool.uv] constraint-dependencies = ["numba>=0.60","llvmlite>=0.43"]` dans voice-forge. Relock des 5.
- **Images figées** : plus aucun `:latest` ni tag roulant — searxng en tag daté `2026.7.5-a6438586a`, uv `0.11.26` (4 Dockerfiles), llama.cpp/neo4j/open-webui **par digest** des images déjà tirées (aucun re-pull). `docker compose config` valide.
- **Outils** : `scripts/download-models.sh` réécrit (saute les fichiers présents), nouveaux `scripts/smoke-embedder.sh` et `scripts/smoke-tts.sh`, `docker-compose.sans-stt.yml` (override, désormais inutile puisque le STT est là — le garder en secours).

## Reprendre ici

1. **Rebuild voice-forge** : `docker compose build voice-forge` — c'est le seul build qui restait cassé, maintenant réparé (numba 0.66.0 / llvmlite 0.48.0, roues cp312, plus de compilation source). ⚠️ **~3 Go** (torch + CUDA) : c'est un gros téléchargement → **accord explicite de l'utilisateur requis, il le lance lui-même** (mémoire `telechargements-manuels-par-utilisateur`). Impasse à connaître avant de re-toucher au lock : `docs/impasses.md`, 2026-07-06.
2. **Premier lancement réel** : `docker compose up -d` (LLM ~2 min à charger). Lancer le Pont hôte **hors Docker** avec le vrai jeton :
   `cd host-bridge && HOST_BRIDGE_TOKEN=<valeur du .env> HOST_BRIDGE_HOST=0.0.0.0 uv run python -m app`.
3. **Smoke-tests** (dès que la stack tourne — l'agent peut les lancer et interpréter) : `scripts/smoke-embedder.sh`, `scripts/smoke-llm.sh` (paye la prémisse différée : qualité du JSON structuré du 35B pour Graphiti), puis enrôler une voix sur `http://127.0.0.1:8100/admin` et `scripts/smoke-tts.sh`.
4. **Config OpenWebUI** (`docs/OPENWEBUI.md`) : audio STT/TTS, personas, Filter mémoire, MCP `http://memory:8200/mcp`.
5. **Scénarios d'acceptation** (détail au handoff 0004) : latence ≤ 2 s, scénario Léa, croisement document, oubli, visualisation du graphe.

**Prémisses différées (échéance : premier lancement réel)** — inchangées depuis 0006, plus une neuve :
- Schéma Cypher de GraphitiMemory (labels/propriétés supposés) et qualité du JSON du 35B Uncensored pour l'extraction (re-grilling du moteur si ça déçoit).
- Adaptateurs réels jamais exécutés (GraphitiMemory, RealWorld, HostBridgeAnnouncer sauf le Pont validé ce jour, `_RealChatterboxEngine`).
- **NEUF — compatibilité torch/GPU** : `chatterbox-tts` épingle `torch 2.6.0` (CUDA 12.4) ; le RTX 5080 est **Blackwell sm_120**, potentiellement non couvert avant torch 2.7+/CUDA 12.8. À vérifier au premier appel TTS GPU ; si `_RealChatterboxEngine` échoue sur le device, c'est un sujet de compatibilité à instruire (pas un bug du code).

## Méthode de travail (inchangée, dans CLAUDE.md)

Analyser → proposer → **attendre validation** → TDD → tests → doc. Tout en français. Jamais de `git commit` par l'agent (**et jamais de Co-Authored-By**). Aucun gros téléchargement (> 100 Mo, images/torch inclus) sans accord explicite au moment même — un « fais tout » ne le couvre pas. `/premisses` avant toute tâche significative, `/impasses` à chaud.

## Suggested skills

- `/premisses` — en début de session : les croyances de ce handoff se vérifient (état des images buildées, voice-forge rebuildé ou non).
- `/run` ou `/verify` — premier lancement réel de la stack (l'étape qui reste), une fois voice-forge rebuildé.
- `/delegate` — pour toute implémentation volumineuse.
- `/handoff` — générer le 0008 en fin de session.
