# Configuration OpenWebUI

Tout se fait par variables d'environnement (déjà dans `docker-compose.yml`) et par l'UI native. **Aucune modification d'OpenWebUI.**

## Variables d'environnement (premier démarrage)

Les variables `AUDIO_*` et `OPENAI_*` du compose ne sont lues **qu'au premier démarrage** (mécanisme PersistentConfig) : ensuite la configuration vit dans la base SQLite d'OpenWebUI et se modifie dans **Admin Panel → Settings → Audio**. Si tu changes le compose après coup, réplique le changement dans l'UI (ou supprime le volume `open-webui-data`).

| Réglage UI (Admin → Settings → Audio) | Valeur |
| --- | --- |
| STT Engine | OpenAI · base URL `http://stt:8080/v1` · clé `sk-local` · modèle `voxtral-mini` |
| TTS Engine | OpenAI · base URL `http://voice-forge:8100/v1` · clé `sk-local` · modèle `tts-1` |
| TTS Voice | une des voix du Voice Forge (le sélecteur se peuple tout seul via `/audio/voices`) |

## Créer un persona (Workspace → Models → +)

1. **Base Model** : le modèle Qwen servi par llama.cpp.
2. **System Prompt** : un prompt « voice-first » (voir `personas/`).
3. **Advanced Params → TTS Voice** : choisir la voix du persona (champ natif ; il écrit `meta.tts.voice`, prioritaire sur le réglage utilisateur et la config globale).

## Presets audio (Settings → Audio, côté utilisateur)

- **Casque** : activer *Allow Voice Interruption in Call* — tu peux couper la parole à l'assistant.
- **Haut-parleurs** : désactiver ce même réglage — sinon l'assistant s'interrompt en s'entendant lui-même.

Un clic pour basculer ; c'est le seul réglage qui distingue les deux presets.

## Mémoire persistante (phase 2)

1. Coller le contenu de `openwebui/functions/memory_filter.py` dans **Admin Panel → Functions → +** (type Filter), l'activer.
2. L'activer **par modèle** sur chaque persona qui doit avoir de la mémoire (éditeur de modèle → Filters). Le persona **off-record** = ne pas l'activer sur ce modèle.
3. Valves disponibles : URL du Memory Forge (`http://memory:8200` en Docker), nombre de faits injectés, budget latence (300 ms, fail-open au-delà).

### Outils recall / forget (MCP)

1. **Admin Panel → Settings → Tools → +** : ajouter le serveur MCP `http://memory:8200/mcp` (transport streamable HTTP).
2. Activer les outils `recall` et `forget` par persona (éditeur de modèle) — jamais sur le persona off-record.
3. `forget` supprime **définitivement** ; sa description impose au LLM d'annoncer ce qu'il va oublier et de n'agir que sur demande explicite.

## Mode appel

Bouton d'appel (casque/téléphone) dans la barre de saisie d'un chat ouvert avec le persona voulu. OpenWebUI gère nativement : VAD, transcription Voxtral, réponse LLM streamée phrase par phrase vers le Voice Forge, lecture audio.
