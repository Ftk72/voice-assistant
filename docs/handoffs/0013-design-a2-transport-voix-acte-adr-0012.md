# Handoff 0013 — Design du transport voix (A2) acté : ADR 0012, contrat DF dessiné

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent
> fait foi. En fin de session, générer le 0014 via `/handoff`.

Date : 2026-07-08 · Remplace le 0012. Session couverte : audit des prémisses
d'A2 (transport voix), puis **grilling de design** (`/grill-with-docs` : grilling
+ domain-modeling) → **ADR 0012** actant le cycle de conversation, l'interruption,
la fixité du persona et le contrat Dialogue Forge↔transport. **Aucune ligne de
code A2** — c'était une session de décision, pas d'implémentation.

## Lire avant tout (fait autorité)

- `docs/adr/0012-transport-voix-cycle-conversation-interruption-contrat-df.md`
  — **LE document de la session** : 5 décisions (micro ouvert + fin par silence ;
  bouton d'abord, mot d'éveil différé navigateur-side ; interruption tronque
  l'historique DF ; persona figé ; voix dans le stream `/tours`) + les 3 ajouts
  de contrat DF. Ne pas rediscuter sans nouveau grilling.
- `docs/roadmap.md` §A2 — le périmètre du transport (Pipecat, VAD, STT/TTS,
  RTVI). L'ADR 0012 le précise.
- `docs/adr/0010-…` (audio par la webview, RTVI) et `docs/adr/0011-…`
  (mémoire user-only, `/clore`) — l'ADR 0012 s'appuie sur les deux.
- `CONTEXT.md` — *Conversation* précisée + *Fenêtre d'écoute de suite* ajoutée
  (⚠️ **modif non commitée**, voir plus bas).

## État git — ce qui est commité, ce qui ne l'est pas

- **Commité** (lots mémoire de la session précédente de ce cycle) : ADR 0011 +
  ontologie 8 types (bddf3d1), CONTEXT mémoire (cb7f641), dialogue-forge capture
  par conversation (ce21925).
- **NON commité, à graver** :
  - `CONTEXT.md` (modifié) — termes A2 (*Conversation*, *Fenêtre d'écoute de suite*) ;
  - `docs/adr/0012-…` (neuf) — l'ADR de cette session ;
  - `docs/handoffs/0012-…` (neuf) — le handoff mémoire, **jamais commité** ;
  - ce handoff `0013-…`.
- `host-bridge/catalog.toml` (non suivi) : **hors** de ces lots, ne pas
  l'inclure sans savoir ce que c'est (présent depuis le début du cycle).

Commande de commit suggérée pour le lot A2-décision (l'utilisateur commite) :
`git add CONTEXT.md docs/adr/0012-*.md docs/handoffs/0012-*.md docs/handoffs/0013-*.md`
puis un message « ADR 0012 : design du transport voix (A2) ; glossaire + handoffs ».

## Ce que la prochaine session peut faire (aucune ne bloque sur un téléchargement)

1. **Squelette `transport-voix/` en TDD** — nouveau composant aux conventions
   forges (modèle memory-forge) : `create_app` + `/health`, **ports** STT / TTS /
   DialogueForge + **adaptateurs factices par défaut**, adaptateur Pipecat réel
   « jamais exécuté ». Pipecat en **extra optionnel** (`uv sync --extra pipecat`,
   pipecat-ai 1.5.0). Le transport ne sert **aucune UI**.
2. **Lot contrat Dialogue Forge** (indépendant, côté dialogue-forge) :
   - `POST /conversations/{id}/interrompre` — tronque le dernier tour assistant
     au préfixe prononcé (décision 3 de l'ADR 0012) ;
   - le stream `/tours` **porte la voix courante** (décision 5).
   - `/clore` : déjà livré (ADR 0011).
3. **Mettre à jour `docs/impasses.md`** via `/impasses` : les deux impasses STT
   **Voxtral** (template Devstral ; « répond au lieu de transcrire ») ont leur
   condition « valide tant que » **tombée** (swap whisper.cpp, commit a7bc69e) —
   à marquer périmées, comme le veut le registre.

## Prémisses différées (audit du 2026-07-08 — vérifier, pas croire)

- **Pont WebRTC WebView2↔Pipecat** : jamais prototypé. Échéance : premier
  end-to-end réel (couplé au front A3 coquille, ou un client navigateur minimal).
  C'est LE risque n°1 d'A2 — la décision « bouton d'abord » (ADR 0012) sert
  précisément à le lever avec **un seul inconnu à la fois**.
- **Import exact `SmallWebRTCTransport` + protocole RTVI** de Pipecat 1.5 : à
  figer à l'écriture de l'adaptateur réel (l'extra `webrtc` existe, le nom de
  classe se confirme sur la doc/le source).
- **Modèle mot d'éveil français (openWakeWord)** : risque ouvert acté ; lot
  ultérieur, navigateur-side (décision 2). Ne pas l'attaquer au premier jet.
- **TTS `/audio/speech` streame-t-il les chunks** (vs buffer complet) ? À mesurer
  au branchement réel ; impacte la latence d'interruption.
- Héritées : `_RealQwen3TTSEngine` jamais exécuté ; vraie voix non enrôlée ;
  obsolescence Graphiti jamais validée (expérience « déménagement », ADR 0011) ;
  8 types d'ontologie jamais vus par l'extraction réelle ; image memory pas
  rebuildée (le `/viz` 3D pas encore servi par Docker).

## Briques vérifiées cette session (se re-vérifient, ne se persistent pas)

- STT whisper.cpp : `/v1/audio/transcriptions`, `--convert`, **batch** (pas de
  partiel → transcription utilisateur affichée après le tour).
- TTS voice-forge : `POST /audio/speech` + `/audio/voices` + `/models`, port 8100.
- Dialogue Forge : port 8600, `/conversations/{id}/tours` NDJSON, `/clore` livré.
- pipecat-ai 1.5.0 (PyPI), extras `webrtc`/`silero`/`openai`/`whisper`, py≥3.11.

## Méthode de travail (inchangée — CLAUDE.md)

Analyser → proposer → attendre validation → TDD → doc. Tout en français.
Jamais de `git commit` par l'agent ; « texte du commit » = commande git
complète. Gros téléchargements lancés par l'utilisateur (dépôt/fichier vérifiés
par API avant de donner la commande). Délégations : évaluer d'abord (les petits
lots contextuels se font mieux inline), brief autoportant, vérification finale.

## Suggested skills

- `/premisses` — en ouverture : l'utilisateur a-t-il commité le lot A2-décision ?
  le pont WebRTC a-t-il été prototypé ? Pipecat installé ?
- `/impasses` — **marquer périmées** les deux impasses STT Voxtral (condition
  tombée) ; consulter avant tout diagnostic audio.
- `/tdd` — squelette `transport-voix` et lot contrat DF, test-first comme
  memory-forge/dialogue-forge.
- `/grilling` — si le branchement réel révèle un fork non anticipé (ex.
  signalisation WebRTC, latence d'interruption).
- `/delegate` — **évaluer d'abord** (le squelette est petit et contextuel :
  probablement inline).
- `/handoff` — générer le 0014 en fin de session.
