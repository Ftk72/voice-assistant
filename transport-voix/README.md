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
  (le pont WebRTC WebView2↔Pipecat n'a **jamais été prototypé** — l'adaptateur
  réel lève `NotImplementedError`, cf. ADR 0012, prémisses différées).

Pipecat est déclaré en extra optionnel (`pipecat`) et **non installé** par
défaut : `uv sync` seul suffit pour développer et tester ce composant.
`uv sync --extra pipecat` est un téléchargement lourd, réservé à l'utilisateur.

Ce composant ne sert aucune UI.

## Lancer les tests

```
cd transport-voix
uv sync
uv run pytest
uv run ruff check .
```
