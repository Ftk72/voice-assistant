# Assets audio statiques

## `accueil.wav`

Joué **tel quel** (frame audio brute, pas de synthèse TTS) à l'ouverture d'une
conversation (`app/transport/pipecat.py`, `on_client_connected`) — remplace
l'ancien accueil synthétisé (« Bonjour, je t'entends. »).

- **Origine** : `ben_1.mp3` fourni par l'utilisateur (racine du dépôt).
- **Format cible** : PCM16 mono 24 kHz (`_charger_wav_pcm16` refuse tout autre
  échantillonnage de bits — WAV déjà décodé, aucune dépendance de décodage
  runtime côté transport).
- **Conversion** (ffmpeg du conteneur voice-forge, pas d'installation locale) :

  ```sh
  docker compose cp ben_1.mp3 voice-forge:/tmp/ben_1.mp3
  docker compose exec -T voice-forge ffmpeg -y -i /tmp/ben_1.mp3 \
    -ar 24000 -ac 1 -sample_fmt s16 -codec:a pcm_s16le /tmp/accueil.wav
  docker compose cp voice-forge:/tmp/accueil.wav app/assets/accueil.wav
  ```

Pour changer le son d'accueil : refaire cette conversion sur le nouveau
fichier, ou pointer `TRANSPORT_VOIX_ACCUEIL_AUDIO_PATH` vers un autre WAV déjà
au format cible.
