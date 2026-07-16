# Handoff 0015 — TTS/STT du pipeline corrigés en code, capture micro déléguée

> Convention : handoffs dans `docs/handoffs/`, seul le plus récent fait foi.
> En fin de session, générer le 0016 via `/handoff`.

Date : 2026-07-09 · Remplace le 0014. Session **courte et ciblée** : les deux
étages OpenAI-compat du pipeline Pipecat (TTS voice-forge, STT whisper.cpp) sont
**corrigés et audités en statique**, et un lot UI (capture micro voice-forge) a
été **délégué à sonnet puis vérifié**. Tout est commité, git propre.

## Ce qui a été fait (3 commits — ne pas re-litiger)

Voir les messages de commit pour le détail ; ne pas le recopier ici.

1. `2c268f9` **TTS Pipecat adapté à voice-forge**. Le blocage n°1 du 0014 est
   levé **en code**. Prémisse tranchée : voice-forge renvoie du **WAV** (pas du
   PCM comme le supposait `OpenAITTSService`). Sous-classe
   `transport-voix/app/transport/tts_voiceforge.py` (`ServiceTTSVoiceForge`) :
   voix passée telle quelle (plus de check `VALID_VOICES`) + réponse routée par
   le helper Pipecat `_stream_audio_frames_from_iterator(strip_wav_header=True)`
   (strip en-tête, détection du rate dans le WAV, resample). Branchée dans
   `transport-voix/app/transport/pipecat.py`.
2. `3fa1c2a` **STT Pipecat en français**. `OpenAISTTService` retombait sur
   `Language.EN` (aucune langue fournie) → il annonçait un audio anglais à
   Voxtral sur un assistant 100 % FR. Câblé sur `Language(s.langue)` (= FR).
3. `f7dbf3f` **voice-forge : enrôlement de la vraie voix par capture micro**
   (lot B2a, délégué). Module `/admin` : `getUserMedia` + `MediaRecorder` →
   `decodeAudioData` → encodage **WAV PCM 16 bits mono en JS pur** (pas de
   transcodage serveur, pas de dépendance). Backend : validation magie WAV
   (415 sinon). Mentions résiduelles d'OpenWebUI nettoyées (ADR 0009).

## Lire avant tout (fait autorité)

- `docs/impasses.md` — **à jour**. L'impasse TTS du 2026-07-09 est marquée
  **levée en code** (avec la vigilance STT désormais **tranchée par
  inspection** : pas de rigidité type-`VALID_VOICES` côté STT). Toujours
  consulter avant tout diagnostic audio/réseau : la media WebRTC est résolue
  par **co-localisation Windows**, les pistes NAT/mirrored/coturn sont payées.
- `docs/adr/0012-*` (transport voix) et `docs/adr/0010-*` (UI coquille).
- `transport-voix/README.md` et `coquille/README.md` — lancement **sur Windows**
  (le setup complet pour rejouer le bout-en-bout est dans le handoff 0014, §Setup).

## Prochaine tâche immédiate — le run réel bout-en-bout sur Windows

Les fixes TTS et STT sont prouvés **en unitaire** (12 tests transport-voix verts,
WAV synthétique), **jamais exécutés bout-en-bout**. Le maillon manquant est le
**run réel** (natif Windows, micro, coquille + Pipecat co-localisés, forges
Docker en marche) — l'agent principal **ne peut pas le lancer** (pas d'accès
Windows/micro). C'est l'utilisateur qui rejoue, en suivant le §Setup du 0014.

Ce que ce run doit confirmer / débloquer :
- **L'annonce d'accueil est audible** (« Bonjour, je t'entends. ») → valide le
  TTS voice-forge de bout en bout (le WAV strip + resample tiennent en réel).
- Puis la **voie entrante** : micro → STT français → Dialogue Forge → TTS.
- **getUserMedia dans WebView2** (avait fonctionné au 0014, à reconfirmer) et
  les événements **RTVI** réels (la pastille est encore un stub visuel).

Si l'audio TTS sort corrompu malgré le strip WAV : suspecter le **sample_rate**
réel de voice-forge vs la sortie du pipeline (le resample est censé couvrir, mais
c'est le premier passage en conditions réelles).

## Lots UI — état réel (surprise de la session)

Le **Front B de `docs/roadmap.md` est en grande partie déjà bâti** — vérifié cette
session, à ne pas re-déléguer à l'aveugle :
- **B1 graphe 3D** : `memory-forge/app/viz/` a déjà `3d-force-graph.min.js`
  vendoré (1,3 Mo, three.js inclus, **aucun téléchargement**), scène + filtres +
  `analyse.py` (communautés/centralité) + tests. Restent des tranches (curseur
  temporel, recherche d'entité, bascule 2D/3D) — à cadrer si besoin.
- **B2 voix** : import fichier + preview + delete existaient ; la **capture
  micro** manquait → faite ce tour (B2a). Restent hors périmètre B2a : **voix
  par défaut/d'annonce** (contrat inter-composants) et **presets audio
  casque/haut-parleurs** (relèvent de la coquille).
- **B3 agenda** : fait (handoff 0014).
- **B4 notifications d'annonces** : **neuf**, mais touche `coquille/pastille.js`
  (SSE/WS time-forge → pastille) → **pas « aucun fichier partagé »** ; à traiter
  quand la pastille passe du stub au réel.

Prochain lot délégable propre le plus évident : **A4 module dialogue** (onglet
console consommant Dialogue Forge REST/NDJSON + événements RTVI) — mais il est
sur le **chemin critique** (couplé au transport live et à RTVI encore stub),
donc **pas un bon candidat à la délégation à froid** tant que RTVI n'est pas réel.

## Vigilances (se re-vérifient, ne se persistent pas)

- **Fixes TTS/STT jamais exécutés bout-en-bout** — cf. tâche immédiate.
- **Capture micro B2a jamais exécutée en navigateur** — seul le contrat serveur
  (201/415/409/422) est testé ; à valider dans WebView2.
- **Pastille = stub visuel**, pas de RTVI réel ; **coquille = placeholder logo**.
- Héritées : vraie voix non encore enrôlée en pratique (VoixDeTest partout,
  y compris `TIME_FORGE_ANNOUNCE_VOICE`) ; `_RealQwen3TTSEngine` (voice-forge) et
  `SubprocessRunner` (host-bridge) jamais exécutés ; 8 types d'ontologie jamais
  vus par l'extraction réelle.
- `host-bridge/catalog.toml` reste **non suivi, hors de tout lot**.

## Méthode (inchangée — CLAUDE.md)

Analyser → proposer → attendre validation → TDD → doc. Tout en français. Jamais
de `git commit` par l'agent ; « texte du commit » = commande git complète
(add + commit), **sans** `Co-Authored-By`. Gros téléchargements lancés par
l'utilisateur. Délégation : cadrer, choisir le modèle, **vérifier soi-même**
(tests + lint relancés, diff confronté au périmètre, fichiers critiques relus).

## Suggested skills

- `/impasses` — **en ouverture** : lire le registre (media résolue, TTS levée en
  code, STT tranchée).
- `/premisses` — avant le run réel, re-vérifier que la stack Docker (STT 8002,
  TTS 8100) et Dialogue Forge (8600) tournent, et le sample_rate réel de
  voice-forge.
- `/delegate` — si une tranche B1 (curseur temporel/recherche) ou un lot voix
  par défaut est cadré ; **évaluer d'abord** la disjonction (aucun fichier
  partagé avec le chemin voix).
- `/handoff` — générer le 0016 en fin de prochaine session.
