---
label: wayfinder:task
statut: clos
assigne: utilisateur (HITL, poste Windows, sessions 2026-07-10 → 2026-07-16)
bloque-par: []
---

# Run réel bout-en-bout sur Windows

## Question

**HITL — le grand débloqueur.** Les fixes TTS (strip WAV `ServiceTTSVoiceForge`)
et STT (langue FR) sont prouvés en unitaire, **jamais exécutés en réel**.
L'agent n'a ni Windows ni micro : c'est l'utilisateur qui joue, checklist en
main (§Setup du handoff 0014, forges Docker + Pipecat et coquille natifs
Windows co-localisés).

À confirmer, dans l'ordre :

1. **Annonce d'accueil audible** (« Bonjour, je t'entends. ») → le TTS
   voice-forge tient en réel (strip WAV + resample). Si l'audio sort corrompu :
   suspecter le sample_rate réel de voice-forge (vigilance handoff 0015).
2. **Voie entrante** : micro → STT français → Dialogue Forge → TTS.
3. **getUserMedia dans WebView2** (avait marché au 0014, à reconfirmer) et
   les **événements RTVI réels** observés (prérequis du ticket « RTVI réel
   dans la pastille »).
4. **Mesures** : latence voix→voix, STT, TTS par tour (référence ancienne
   stack : 2,88 s) — alimente l'arbitrage latence (carte, fog).

Résolution = compte rendu factuel (ce qui a marché, mesures, anomalies), qui
graduera le fog « ce que le run réel révélera » en tickets correctifs.

## État intermédiaire (2026-07-10, premier essai)

Logs du premier essai fournis par l'utilisateur (`logs-tests/transport.log`,
`coquille.log`) :
- **Acquis** : Pipecat 1.5.0 tourne sur Windows, pipeline complet construit,
  ICE `connected` en localhost, **TTS voice-forge synthétise sans erreur**
  (TTFB 2,04 s — l'annonce d'accueil est partie vers la sortie WebRTC ;
  audibilité/qualité à confirmer par l'utilisateur).
- **Blocage n°1 (résolu en code)** : la coquille échouait au préflight CORS
  (`OPTIONS /offer → 405`, origine `http://tauri.localhost`) → middleware CORS
  ajouté au transport (`app/main.py`, origines dans `Settings.cors_origines`,
  TDD). Nécessite un **redémarrage du transport** côté Windows.
- **Blocage n°2 (ouvert)** : dans la session /prototype, **aucune trame audio
  micro reçue** (« No audio frame received », récepteur désactivé après 2 s
  d'inactivité) — aucune activité STT ensuite. À requalifier au prochain essai
  (permission micro tardive ? l'utilisateur n'a pas parlé ? vraie panne de
  voie entrante ?).
- Au passage : `turn_url` par défaut vidé (le coturn supprimé ralentissait
  l'ICE gathering de ~5 s).

## Deuxième itération (2026-07-10, après retour utilisateur)

- **Accueil entendu mais grésillant** → cause prouvée : voice-forge renvoie du
  WAV **float32** (code 3, données à l'offset 80, mesuré en direct sur
  `/audio/speech`), alors que le helper Pipecat strippe 44 octets fixes et
  suppose du PCM 16 bits. Double correctif :
  1. transport : `NormaliseurWavPCM16` (TDD, 4 tests) branché dans
     `ServiceTTSVoiceForge` — en-tête canonique 44 o + float32→int16 à la
     volée ; effectif au prochain redémarrage du transport ;
  2. voice-forge : `chatterbox.py` sauve désormais en PCM 16 bits explicite —
     effectif au prochain rebuild de l'image (code cuit dans l'image).
- **« J'ai parlé mais pas de réponse »** : les `OPTIONS /offer → 405` répétés
  montrent que l'essai coquille s'est fait avec l'ancien processus transport
  (fix CORS non chargé). La voie micro reste **non qualifiée** — à retester
  après redémarrage du transport.
- L'agent recherche mot d'éveil a été arrêté par l'utilisateur (aucune note
  produite) — le ticket 0009 redevient non réclamé.

## Résolution (2026-07-16) — chaîne voix validée bout-en-bout

Le run réel a été mené à terme au poste Windows (« ça marche et ça répond »,
puis « c'est validé »). La nouvelle stack **parle** : conversation ouverte au
bouton, micro → VAD → STT français → Dialogue Forge → TTS voice-forge → retour
audio dans la coquille.

Ce que le run a révélé (pièges levés en cours de route, chacun corrigé) :
CORS coquille (405 sur `/offer`), VAD Pipecat 1.5 (`vad_analyzer=` ignoré →
`VADProcessor`), WAV float32 grésillant (`NormaliseurWavPCM16`), timeout httpx
au premier tour, montages vides post-reboot. `getUserMedia`/WebView2 confirmé,
événements RTVI confirmés (ticket 0007). Détails dans les handoffs 0016/0017 et
`docs/impasses.md`.

Mesures partielles observées : STT TTFB 0,3-0,5 s, temps de traitement STT
0,13-0,32 s, transcriptions françaises exactes. **Latence voix→voix en régime
non encore mesurée** : premier tour à froid lent (préfill LLM ~13 s, connu) —
la mesure propre face aux références de l'ancienne stack (2,88 s) reste à faire
au ticket 0011 (arbitrage latence, cible ≤ 2 s).
