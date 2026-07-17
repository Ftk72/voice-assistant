# Voice Forge

API TTS compatible OpenAI, consommée par le **transport voix** (client TTS
OpenAI de Pipecat, cf. `ServiceTTSVoiceForge`) à base URL custom. Seul
composant custom du projet (voir `../docs/adr/`).

## Lancer

```bash
uv sync
uv run python -m app        # http://127.0.0.1:8100
```

Configuration par variables d'environnement (préfixe `VOICE_FORGE_`) : `VOICES_DIR` (défaut `voices`), `HOST` (défaut `127.0.0.1`), `PORT` (défaut `8100`), `PROVIDER` (`fake` par défaut, `chatterbox` en production), `DECODEUR` (`fake` par défaut = WAV seul, `ffmpeg` = dépôt multi-format), `CACHE_DIR` (cache audio disque, désactivé si absent).

## Mini-page d'admin

`/admin` — import (nom + échantillon audio), aperçu (synthétisé en direct, hors cache disque) et suppression des voix. API sous `/admin/api/voices`.

L'import accepte un WAV (stocké tel quel) ou tout autre conteneur (mp3, m4a, ogg, flac…) **décodé en WAV de référence** via le décodeur sélectionné par `VOICE_FORGE_DECODEUR` (`fake` par défaut = WAV uniquement ; `ffmpeg` = multi-format, ffmpeg requis dans l'image). Format indécodable → 415.

## Contrat HTTP (compatible OpenAI)

- `GET /audio/voices` → `{"voices": [{"id", "name"}]}` — peuple le sélecteur de voix du client.
- `POST /audio/speech` — payload OpenAI `{"model", "input", "voice"}` → audio WAV.
- Les deux routes existent aussi sous `/v1/…` (la base URL du client peut inclure le préfixe ou non).

## Voix

Une voix = un dossier `voices/NomVoix/` contenant au minimum `speaker.wav` (échantillon de référence pour le clonage). Le scan est fait à chaque requête : une voix déposée est exposée par l'API (et le sélecteur du client) sans redémarrage.

## Providers

`app/providers/base.py` définit `BaseTTSProvider` (`synthesize(text, speaker_wav) -> bytes`).

- `FakeProvider` — WAV silencieux, sans GPU (défaut ; développement et tests).
- `ChatterboxProvider` — Chatterbox Multilingual (ADR 0002) : clonage zero-shot depuis `speaker.wav`, paramètres par voix via `config.json` (`language`, `exaggeration`, `cfg_weight`), chargement paresseux du modèle. Dépendances lourdes dans l'extra : `uv sync --extra chatterbox` (tire torch, ~2,5 Go). ⚠️ L'adaptateur du vrai modèle (`_RealChatterboxEngine`) n'a jamais été exécuté — à valider à la première installation.
- `CachedProvider` — décorateur de cache disque (activé par `VOICE_FORGE_CACHE_DIR`).

## Tests

```bash
uv run pytest
uv run ruff check .
```
