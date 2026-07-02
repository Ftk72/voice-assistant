# Assistant vocal local

Assistant vocal 100 % local (français, voix clonées) avec **OpenWebUI comme unique interface**. Zéro fork, zéro modification d'OpenWebUI : tout passe par ses mécanismes natifs.

```
┌─────────────────────────── Docker ────────────────────────────┐
│                                                               │
│  openwebui (UI, seule exposée : http://127.0.0.1:3000)        │
│     │ chat        │ voix→texte        │ texte→voix            │
│     ▼             ▼                   ▼                       │
│  llm          stt                voice-forge                  │
│  llama.cpp    llama.cpp          FastAPI + Chatterbox         │
│  Qwen3.6-35B  Voxtral Mini       clonage de voix (~3 Go VRAM) │
│  (~6 Go VRAM) (~3 Go VRAM)       admin : 127.0.0.1:8100/admin │
└───────────────────────────────────────────────────────────────┘
```

Décisions techniques : [docs/adr/](docs/adr/) · Glossaire : [CONTEXT.md](CONTEXT.md) · Critères d'acceptation : [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)

## Installation

1. **Télécharger les modèles** (~26 Go, une seule fois) : `./scripts/download-models.sh`
   (vérifier les noms de dépôts Hugging Face indiqués dans le script).
2. **Construire et lancer** : `docker compose up -d --build`
   (le build du Voice Forge télécharge torch/torchaudio, ~2,5 Go).
3. **Ouvrir** http://127.0.0.1:3000 — la config audio (STT/TTS) est injectée au premier démarrage ; détails et personas : [docs/OPENWEBUI.md](docs/OPENWEBUI.md), [personas/](personas/).

## Ajouter une voix

- Déposer un dossier `voices/MaVoix/` contenant un `speaker.wav` de quelques secondes, **ou** passer par la mini-page d'admin http://127.0.0.1:8100/admin (import, aperçu, suppression).
- La voix apparaît immédiatement dans OpenWebUI (Settings → Audio et éditeur de persona), sans redémarrage.
- Optionnel : un `config.json` à côté du `speaker.wav` surcharge les paramètres (`language`, `exaggeration`, `cfg_weight`).

## Presets audio

- **Casque** : Settings → Audio → activer *Allow Voice Interruption in Call*.
- **Haut-parleurs** : désactiver ce réglage (sinon l'assistant s'entend et s'interrompt).

## Éthique et sécurité

- Voix clonées de personnes réelles : usage strictement personnel, aucune diffusion des sorties audio.
- Seul OpenWebUI est publié ; LLM, STT et Voice Forge sont liés à `127.0.0.1`.
- Aucun appel réseau sortant à l'exécution (hors téléchargement initial).

## Développement (Voice Forge)

Voir [voice-forge/README.md](voice-forge/README.md) — `uv run pytest` (22 tests, sans GPU grâce au provider factice).

## Reste à faire (jour de bonne connexion)

1. `./scripts/download-models.sh` (vérifier les dépôts HF) puis `docker compose up -d --build`.
2. Valider la config Audio dans OpenWebUI et créer les personas.
3. **Mesurer la latence** fin de parole → début de réponse (cible ≤ 2 s, docs/ACCEPTANCE.md) et ajuster (`--n-cpu-moe`, contexte, streaming TTS).
4. Vérifier l'API réelle de `chatterbox-tts` (l'adaptateur `_RealChatterboxEngine` est écrit d'après la doc, jamais exécuté).
