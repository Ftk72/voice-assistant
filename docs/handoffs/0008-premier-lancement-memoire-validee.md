# Handoff 0008 — Premier lancement réel : stack verte, mémoire validée de bout en bout ; reste OpenWebUI (navigateur) et la voix

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent fait foi. En fin de session, générer le 0009 via `/handoff`.

Date : 2026-07-06 · Remplace le 0007. Session couverte : **premier lancement réel de la stack** (elle n'avait jamais tourné), correctifs post-lancement, puis validation complète de la chaîne mémoire (Graphiti réel). **Tout est commité par l'utilisateur** — 5 commits : `09e0430`, `792bc96`, `49aaf33`, `9a8f52c`, `f0e89c8` (lire `git log 00c6717..f0e89c8` plutôt que de me croire) ; arbre propre.

## Lire avant tout (fait autorité)

- `CLAUDE.md` · `CONTEXT.md` · `docs/adr/` · `docs/ACCEPTANCE*.md`
- **`docs/impasses.md`** — 2 entrées neuves du 2026-07-06 : raisonnement Qwen3.6 (`--reasoning off` obligatoire) et RAG OpenWebUI (~1 Go HF sans `RAG_*`/`OFFLINE_MODE`). Consulter avant tout diagnostic.
- Les 5 commits de la session portent tout le diff, avec des messages détaillés — ne pas les redécrire.

## État : la stack TOURNE (laissée up), 10 services healthy

- **Tous les services sont healthy** : openwebui, llm, stt, embedder, voice-forge, memory, neo4j, searxng, world, time. Le Pont hôte tourne **hors Docker** (port 8500) — relancer après reboot : `cd host-bridge && HOST_BRIDGE_TOKEN=<.env> HOST_BRIDGE_HOST=0.0.0.0 uv run python -m app`.
- **LLM** : `--reasoning off` indispensable (impasse) ; complétion ~0,7 s en régime (critère ≤ 2 s tenu), extraction JSON contrainte valide. GPU RTX 5080 vue, VRAM tendue (15,5/16,3 Go).
- **Mémoire (le gros de la session) — chaîne Graphiti réelle validée** : épisode → extraction différée (~25-40 s) → recherche (~25 ms) → voisinage → oubli sélectif → recall/forget MCP. Extraction **en français** (point d'extension `get_extraction_language_instruction` remplacé — `memory-forge/app/graph/francais.py`), provenance réelle conversation/document dans `/search`, ontologie de types (`ontologie.py` : Activite/Personne/Lieu) + `temperature=0` qui fiabilisent l'épisode court (0/5 → 4/5 avec fait extrait). **Scénario croisement démontré** : le voisinage de « judo » relie Léa (conversation) et judo-club.md (document).
- **Le graphe contient des données de démo** (Léa/judo/natation + document `documents/judo-club.md`) laissées exprès pour l'exploration visuelle : Neo4j Browser `http://127.0.0.1:7474`, `http://127.0.0.1:8200/viz`.
- Adaptateurs désormais **validés en réel** : GraphitiMemory, le Pont hôte. Toujours **jamais exécutés** : `_RealChatterboxEngine.generate()` (le service charge et répond sain, mais aucune synthèse n'a tourné — pas de voix enrôlée), RealWorld, HostBridgeAnnouncer, tout OpenWebUI côté usage.

## Choses à savoir (constatées, pas graves)

- Chaque ré-ingestion d'un document ajoute un nœud `Episodic` doublon (Graphiti ne déduplique pas les épisodes ; les faits, si). Bénin, s'accumule.
- Rebuild memory : BuildKit retélécharge ~24 Mo de paquets malgré le lock inchangé (cache de couche non réutilisé) — sous le seuil, non instruit.
- L'image OpenWebUI embarque 265 Mo de cache modèles **dans l'image même** (pas un téléchargement runtime ; `OFFLINE_MODE=true` bloque le reste).
- Les variables OpenWebUI sont du PersistentConfig (premier démarrage seulement) ; le volume a été réinitialisé ce jour pour les appliquer — tout changement ultérieur passe par l'UI ou un nouveau reset du volume.
- Extraction sur épisode court : 4/5, pas 5/5 — variabilité résiduelle acceptée pour l'instant.

## Reprendre ici

1. **Config OpenWebUI dans le navigateur** (`http://127.0.0.1:3000`, guide : `docs/OPENWEBUI.md`) : compte admin, vérifier Settings→Audio (pré-rempli par le compose), persona voice-first, coller la Filter `openwebui/functions/memory_filter.py`, serveur MCP `http://memory:8200/mcp` (⚠️ trailing slash si test manuel), outils recall/forget par persona.
2. **Enrôler une voix** (`http://127.0.0.1:8100/admin`, wav de quelques secondes) puis `scripts/smoke-tts.sh` — **paye la prémisse torch/Blackwell** : chatterbox épingle torch 2.6.0/CUDA 12.4, le RTX 5080 est sm_120 ; le chargement passe, la synthèse est le vrai test. Échec device = sujet de compatibilité, pas un bug.
3. **Scénarios d'acceptation de vive voix** (`docs/ACCEPTANCE-MEMOIRE.md`, `docs/ACCEPTANCE.md`) : mode appel, latence totale ≤ 2 s, injection ≤ 300 ms via la Filter, scénario Léa au micro, persona off-record.
4. Chantiers non urgents : dédoublonnage des nœuds `Episodic`, 5/5 sur épisode court, `models/voxtral-tts-q4.gguf` (piste TTS future, nécessiterait un ADR).

**Prémisses différées (échéance : premier usage vocal réel)** : synthèse Chatterbox sur sm_120 (jamais exécutée) ; Filter mémoire et MCP dans OpenWebUI réel (écrits, jamais branchés) ; qualité du recall injecté en conversation ; latence bout-en-bout au micro.

## Méthode de travail (inchangée, dans CLAUDE.md)

Analyser → proposer → **attendre validation** → TDD → tests → doc. Tout en français. Jamais de `git commit` par l'agent (et jamais de Co-Authored-By). Aucun téléchargement > 100 Mo sans accord explicite au moment même. L'utilisateur privilégie la délégation (`/delegate`) pour les lots bornés — briefs détaillés, vérification par l'agent principal, `SendMessage` pour prolonger un subagent qui a le contexte.

## Suggested skills

- `/premisses` — en début de session : vérifier que la stack tourne encore (reboot ?), que le Pont hôte est relancé, l'état du graphe de démo.
- `/impasses` — consulter avant tout diagnostic ; capturer à chaud toute piste morte.
- `/verify` ou `/run` — pour le premier test vocal réel (mode appel OpenWebUI).
- `/delegate` — lots bornés (le pattern de la session : brief + vérification indépendante).
- `/handoff` — générer le 0009 en fin de session.
