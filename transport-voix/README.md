# transport-voix

Couche transport voix (ADR 0012) : relie la coquille (micro/haut-parleurs,
WebRTC) aux moteurs STT/TTS et à l'orchestrateur Dialogue Forge. Bâtie sur
Pipecat.

## Ports / adaptateurs

Quatre ports, chacun avec un adaptateur factice (par défaut, zéro réseau,
utilisé par les tests) et un adaptateur réel (jamais exécuté à ce jour) :

- **STT** (`app/stt/`) — `STTFactice` / `STTWhisperCpp` (whisper.cpp, batch).
- **TTS** (`app/tts/`) — `TTSFactice` / `TTSVoiceForge` (voice-forge).
- **Dialogue** (`app/dialogue/`) — `ClientDialogueFactice` /
  `ClientDialogueREST` (client du Dialogue Forge ; le contrat REST/NDJSON est
  finalisé dans un lot parallèle).
- **Transport** (`app/transport/`) — `TransportFactice` / `TransportPipecat`
  (pipeline SmallWebRTC → VAD → STT → Dialogue Forge → TTS, calé sur l'API
  vérifiée de Pipecat 1.5). Le pont WebRTC WebView2↔Pipecat n'a **jamais été
  prototypé** (ADR 0012, risque n°1) : ce code est **jamais exécuté à ce jour**,
  à valider au premier run réel.

Pipecat est déclaré en extra optionnel (`pipecat`) et **non installé** par
défaut : `uv sync` seul suffit pour développer et tester ce composant.
`uv sync --extra pipecat` est un téléchargement lourd, réservé à l'utilisateur.

Ce composant ne sert aucune UI de dialogue (front A4, servi par le Dialogue
Forge). Il expose seulement le signaling WebRTC `POST /offer` et un client de
prototypage `GET /prototype` (outil de dev pour valider le pont).

## Lancer les tests (sans Pipecat)

```
cd transport-voix
uv sync
uv run pytest
uv run ruff check .
```

## Lancer le pipeline réel (jamais exécuté à ce jour)

Prérequis : whisper.cpp (STT), voice-forge (TTS) et le Dialogue Forge doivent
tourner (cf. `docker-compose.yml` du dépôt). Puis, côté utilisateur :

```
cd transport-voix
uv sync --extra pipecat            # téléchargement lourd — lancé par l'utilisateur
TRANSPORT_VOIX_TRANSPORT_BACKEND=pipecat \
TRANSPORT_VOIX_STT_BACKEND=whispercpp \
TRANSPORT_VOIX_TTS_BACKEND=voiceforge \
TRANSPORT_VOIX_DIALOGUE_BACKEND=rest \
  uv run python -m app
```

Ouvrir `http://127.0.0.1:8700/prototype` dans un navigateur (ou la WebView2 de
la coquille), appuyer sur « Parler ». C'est le point où se lèvent les prémisses
différées de l'ADR 0012 (pont WebRTC, imports Pipecat exacts, latence
d'interruption).
