---
label: wayfinder:task
statut: ouvert
assigne: agent principal (session 2026-07-17, volet dépôt multi-format AFK)
bloque-par: []
---

# Atelier d'enrôlement de la vraie voix (capture micro + dépôt multi-format)

## Question

**Re-cadré au re-wayfinding du 2026-07-17** (l'ancien 0005 « capturer la vraie
voix + basculer les consommateurs + vérifier à l'oreille » est éclaté : la
bascule des consommateurs part en 0015, l'audible dépend du clonage réel 0012).

Faire de `/admin` de voice-forge un **atelier d'enrôlement** — geste d'atelier
rare, technique (choix utilisateur : enrôlement séparé de la sélection
grand-public 0014) :

1. **Capture micro navigateur** (`getUserMedia` + encodage WAV JS pur) : lot
   B2a, **codé et jamais exécuté en navigateur**. Un navigateur Windows atteint
   voice-forge via mirrored/localhost (pas besoin de la coquille). HITL.
2. **Dépôt multi-format** — aujourd'hui `import_voice` refuse tout ce qui n'est
   pas RIFF/WAVE (415, cf. `app/routes/admin.py`). Accepter mp3/ogg/flac/m4a…
   et **décoder → WAV de référence** (`voices/NomVoix/speaker.wav`).
   - **Décision à trancher dans le ticket** : où décoder ? ffmpeg dans l'image
     voice-forge (binaire CPU, aucun souci sm_120) vs lib Python
     (soundfile/audioread/pydub). TDD **ports/adaptateurs** (pattern
     memory-forge) : port de décodage + adaptateur factice (défaut, tests) +
     adaptateur réel documenté.
3. **Nommage, aperçu, suppression** — déjà en place (`VoiceManager`,
   `preview_voice`) ; l'aperçu **audible** dépend du clonage réel (0012), mais
   la tuyauterie se teste sur `FakeProvider`.

## Périmètre

- voice-forge : accepter le multi-format à l'import (décodage → speaker.wav),
  TDD ports/adaptateurs ; page `/admin` (capture + dépôt).
- **Hors périmètre** : entendre le clone réel (0012), la bascule des
  consommateurs (0015), la sélection grand-public (0014).

## Avancement (session 2026-07-17) — volet dépôt multi-format livré (AFK)

- **Décision de décodage tranchée : ffmpeg en sous-processus.** `soundfile` seul
  ne décode ni mp3 ni m4a ; ffmpeg est le seul chemin robuste multi-format
  (binaire CPU, aucun enjeu sm_120). Choix confirmé par l'utilisateur.
- **Livré en TDD ports/adaptateurs** : `app/decodeurs/` — port `DecodeurAudio`
  (`base.py`), `DecodeurFactice` (défaut/tests, refuse tout non-WAV : un build
  sans ffmpeg n'accepte que le WAV), `DecodeurFfmpeg` (**réel, jamais exécuté à
  ce jour** — cible WAV PCM16 mono 24 kHz, à confirmer contre Chatterbox),
  factory pilotée par `VOICE_FORGE_DECODEUR`.
- Route d'import : WAV stocké tel quel ; tout autre format → décodé, sinon 415.
  Dockerfile : `ffmpeg` ajouté à l'image ; compose : `VOICE_FORGE_DECODEUR=ffmpeg`.
  UI `/admin` : `accept` ouvert aux formats courants. **42 tests verts, ruff clean.**
- **Dépôt multi-format validé au réel le 2026-07-17** (« tout fonctionne ») : un
  mp3 déposé via `/admin` (navigateur Windows → voice-forge Docker) est décodé
  par ffmpeg et enrôlé, visible dans la liste des voix. `DecodeurFfmpeg` **a
  tourné pour de vrai** (n'est plus « jamais exécuté »). Piège Dockerfile évité :
  ffmpeg placé **après** le `uv sync` chatterbox pour ne pas invalider sa couche.
- **Restant sous ce ticket (HITL, poste Windows)** : la capture micro navigateur
  (point 1, jamais exécutée en navigateur) et la vérification **à l'oreille** (le
  format cible 24 kHz mono du décodage n'est pas prouvé compatible Chatterbox —
  l'aperçu audible relève du clonage réel, ticket 0012).

## Critère de clôture

Depuis un navigateur Windows sur `/admin` : j'enrôle une voix soit en capturant
au micro, soit en déposant un mp3 ; elle apparaît dans la liste ; anomalies de
capture micro en navigateur (s'il y en a) capturées à chaud dans
`docs/impasses.md`.
