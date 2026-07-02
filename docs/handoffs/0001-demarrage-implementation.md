# Handoff 0001 — Assistant vocal local sur OpenWebUI

> Convention du projet : les handoffs sont versionnés dans `docs/handoffs/` avec un numéro croissant. **Seul le dernier (numéro le plus élevé) fait foi** — voir `docs/handoffs/README.md`. En fin de session, générer le suivant via `/handoff`.

Date : 2026-07-02 · Session précédente : analyse d'architecture + session de grilling complète (8 questions, toutes résolues). **La phase de décision est terminée. La prochaine session commence l'implémentation : « go étape 1 ».**

## Objectif du projet

Assistant vocal 100 % local (français, voix clonées sélectionnables instantanément) avec OpenWebUI comme unique interface. Règle absolue : **zéro fork, zéro modification d'OpenWebUI** — tout passe par ses mécanismes natifs (moteurs STT/TTS « openai » à base URL custom, `model.info.meta.tts.voice`, mode appel natif).

## Répertoires

- **Projet (tout le travail va ici)** : `/home/ftk/voice-assistant/` — contient déjà `CONTEXT.md` (glossaire), `docs/adr/0001..0004` (décisions techniques), `docs/ACCEPTANCE.md` (critères d'acceptation, latence ≤ 2 s, scénarios). **Lire ces fichiers avant toute chose — ils font autorité, ne pas les redériver.**
- **Clone lecture seule** : `/home/ftk/openwebui/` (OpenWebUI v0.10.2, commit ecd48e2) — sert uniquement à consulter le code source.
- Machine : Windows 11 + WSL2, RTX 5080 16 Go VRAM, 64 Go RAM, Docker Desktop.

## Points d'intégration OpenWebUI vérifiés (non documentés ailleurs — conserver)

- TTS : dispatcher `_TTS_ENGINES` dans `backend/open_webui/routers/audio.py:546` ; moteur `openai` accepte une base URL custom.
- **Voix : si moteur TTS = `openai` avec base URL non-OpenAI, OpenWebUI interroge `{base_url}/audio/voices` et peuple son sélecteur natif** (`audio.py:1343-1357`, réponse attendue `{"voices": [{"id", "name"}]}`). C'est le contrat que le Voice Forge doit honorer, avec `/audio/speech` (POST, payload OpenAI : `model`, `input`, `voice`).
- STT : moteur `openai` → POST multipart sur `{base_url}/audio/transcriptions` (`audio.py:644`).
- Voix par persona : priorité `model.info.meta.tts.voice` > réglage user > config globale (`src/lib/components/chat/MessageInput/CallOverlay.svelte:385-395`).
- Mode appel natif : `CallOverlay.svelte` (VAD, découpage phrase par phrase, réglage `voiceInterruption`).
- Cache TTS : OpenWebUI hache `body + engine + model` et met en cache les mp3 — les aperçus de voix doivent passer par la mini-page du Voice Forge, pas par OpenWebUI.

## Architecture décidée (détails et justifications dans les ADR)

4 conteneurs : `openwebui` (SQLite, ni Postgres ni Redis) · `llm` = llama.cpp + Qwen3.6-35B-A3B Q4_K_M, experts MoE en RAM (`--n-cpu-moe`, ~6 Go VRAM) · `stt` = llama.cpp + Voxtral Mini GGUF (~3 Go) · `voice-forge` = **seul code custom** : FastAPI, `BaseTTSProvider` → `ChatterboxProvider` (Chatterbox Multilingual, MIT), Voice Manager (scan auto de `voices/NomVoix/{speaker.wav,config.json,metadata.json}`), mini-page d'admin des voix. Services techniques liés à `127.0.0.1` uniquement.

## Plan validé par l'utilisateur

1. Squelette Voice Forge (FastAPI, Pydantic, typing, provider factice, tests) — **prochaine étape**
2. ChatterboxProvider (synthèse + clonage zero-shot, cache, logs)
3. docker-compose (4 services, GPU, healthchecks, scripts modèles) + **mesure de latence vs cible ≤ 2 s**
4. Config OpenWebUI + personas voice-first (prompts oraux sans markdown, `meta.tts.voice`)
5. Mini-page d'admin des voix (import, clonage, aperçu, suppression)
6. Documentation (README, guides, presets casque/haut-parleurs)

## Méthode de travail exigée par l'utilisateur

- Par étape : analyser → proposer → expliquer → **attendre validation** → coder → tests → documentation. Ne jamais coder sans validation.
- Toujours réutiliser l'existant d'OpenWebUI ; ne jamais réécrire une fonctionnalité présente ; parler le dialecte OpenAI exact.
- L'utilisateur est francophone — répondre en français.
- Maintenir `CONTEXT.md` et les ADR au fil des décisions (glossaire = zéro implémentation ; ADR seulement si irréversible + surprenant + vrai compromis).

## Suggested skills

- `/grilling` (ou `/grill-with-docs`) — si une nouvelle décision d'architecture surgit en cours d'implémentation, la passer au grilling plutôt que trancher seul.
- `/domain-modeling` — pour maintenir CONTEXT.md/ADR pendant le code (déjà appliqué jusqu'ici).
- `/tdd` — pour le développement du Voice Forge (l'utilisateur exige des tests unitaires).
- `/handoff` — en fin de session, régénérer un handoff pour la suite.

Les skills sont installés côté WSL dans `/home/ftk/.claude/skills/` (copiés depuis Windows ; copie, pas symlink).
