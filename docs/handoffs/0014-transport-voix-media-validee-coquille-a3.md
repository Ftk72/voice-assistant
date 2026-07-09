# Handoff 0014 — Transport voix bout-en-bout : media WebRTC validée, coquille A3 amorcée

> Convention : handoffs dans `docs/handoffs/`, seul le plus récent fait foi.
> En fin de session, générer le 0015 via `/handoff`.

Date : 2026-07-09 · Remplace le 0013. Session **très longue et opérationnelle** :
implémentation A2 (transport voix Pipecat réel), délégations (B3 agenda,
conteneurisation, coquille A3), et surtout **le premier bout-en-bout réel** qui a
levé le risque n°1 de l'ADR 0012.

## LE résultat de la session (à ne pas re-litiger)

**La media WebRTC passe.** En exécutant transport-voix (Pipecat) **et** la coquille
(WebView2) tous deux en **natif Windows**, la connexion s'établit (`connected`) et
le pipeline tourne jusqu'au TTS. Le pont WebView2↔Pipecat (risque n°1) est
**validé**. Détails et péremption dans `docs/impasses.md` (entrée du 2026-07-09).

**Décision d'architecture actée** (via `AskUserQuestion`) : le **transport-voix et
la coquille tournent en natif Windows** ; les forges lourdes restent en
**WSL2/Docker**, jointes en HTTP (le TCP traverse via WSL `networkingMode=mirrored`).
C'est une entorse assumée à « tout conteneuriser » (comme host-bridge, ADR 0008) —
à graver dans un ADR court si tu veux la figer. `coturn` a été ajouté puis rendu
**inutile** par la co-localisation (laissé dormant dans le compose).

## Lire avant tout (fait autorité)

- `docs/impasses.md` — **à jour**. Contient : media WebRTC **RÉSOLUE** (co-loc
  Windows) ; et le **prochain blocage** (voir plus bas). Consulter avant tout
  diagnostic audio/réseau : les pistes NAT / mirrored+mDNS / mirrored+firewall /
  coturn-bridge sont **déjà payées**, ne pas les refaire.
- `docs/adr/0012-*` (transport voix) et `docs/adr/0010-*` (UI coquille/pastille).
- `transport-voix/README.md` et `coquille/README.md` — comment lancer chaque
  composant **sur Windows** (prérequis, chemins `\\wsl.localhost`, venv séparé).

## Prochaine tâche immédiate — le TTS refuse la voix

Au premier run, `OpenAITTSService` de Pipecat **valide la voix contre l'énum
OpenAI** (`VALID_VOICES`) et rejette « VoixDeTest » **avant tout appel réseau**
(cf. `.../pipecat/services/openai/tts.py:252`). Donc la voix voice-forge ne passe
pas. Fix (détaillé dans `docs/impasses.md`) :

1. **Sous-classer `OpenAITTSService`** : override `run_tts` en retirant le check
   `VALID_VOICES` et en passant `self._settings.voice` tel quel. Le reste (POST
   `/audio/speech`, streaming, frames) est réutilisable.
2. **Vérifier le format de sortie de voice-forge** : `run_tts` demande
   `response_format:"pcm"` et traite les octets comme du **PCM brut à
   `self.sample_rate`, mono**. Si voice-forge ne renvoie pas du PCM à ce rate
   → audio corrompu. (Inspection interrompue : voir `voice-forge/app/routes/`.)
3. **Anticiper le même piège sur `OpenAISTTService`** (whisper.cpp) — non atteint
   au run (l'erreur TTS survient sur l'annonce d'accueil, avant toute parole).

Le brancher dans `transport-voix/app/transport/pipecat.py` (remplacer
`OpenAITTSService` par la sous-classe). Tests factices restent verts sans Pipecat.

## État git — 4 lots NON commités (texte de commit fourni en fin de conversation)

1. **time-forge B3 agenda** (`time-forge/app/viz`, `routes/api.py`, test).
2. **transport-voix A2** (`transport-voix/`, `docs/impasses.md`) — pipeline réel,
   `/offer`, `/prototype`, client ICE par défaut.
3. **Conteneurisation** (`docker-compose.yml`, `coturn/`, `dialogue-forge/Dockerfile`).
4. **Coquille A3** (`coquille/`) — inclut `coquille/logo.png`, **placeholder bleu à
   remplacer**.

Vérifier `git status` avant de commiter (certains lots ont pu être commités en
séance). `host-bridge/catalog.toml` reste **hors** de tout lot.

## Ce qui a été vérifié cette session (se re-vérifie, ne se persiste pas)

- **transport-voix** : pipeline Pipecat 1.5.0 **construit et exécuté** (imports,
  signatures, construction sans warning après 3 corrections d'API — cf. commits) ;
  10 tests verts sans l'extra pipecat (imports lourds différés).
- **coquille** : **compile et se lance sur Windows** (Tauri v2, fenêtres console +
  pastille, tray, raccourci `Ctrl+Alt+Espace`). API Tauri v2 groundée sur la doc.
- **dialogue-forge conteneurisée** : image bâtie, `create_app` OK dans le conteneur
  (personas montés, backends openai/rest/mcp). Non démarrée sur 8600 (conflit avec
  l'instance `uv` — l'utilisateur arrête l'une ou l'autre).
- **B3 agenda time-forge** : 34 tests verts, page `/agenda`, zéro CDN.

## Setup Windows (pour rejouer le bout-en-bout)

- **Transport** : `winget install astral-sh.uv Python.Python.3.12` ; puis, dans
  PowerShell, `$env:UV_PROJECT_ENVIRONMENT="C:\venvs\transport-voix"` (venv séparé
  du `.venv` Linux), `cd \\wsl.localhost\Ubuntu-24.04\home\ftk\voice-assistant\transport-voix`,
  `uv sync --extra pipecat`, exporter les 4 `TRANSPORT_VOIX_*_BACKEND`, `uv run python -m app`.
- **Coquille** : Rust MSVC (`winget install Rustlang.Rustup` + `rustup default
  stable-msvc`) **et** « Microsoft C++ Build Tools » (workload VCTools + Windows SDK,
  sinon `link.exe not found`) ; puis `$env:CARGO_TARGET_DIR="C:\cargo-target\coquille"`,
  `cargo install tauri-cli --version "^2.0.0" --locked`, `cargo tauri icon logo.png`,
  `cargo tauri dev`.
- Prérequis WSL : la **stack Docker doit tourner** (STT 8002, TTS 8100) et
  **Dialogue Forge up** (8600). `networkingMode=mirrored` déjà en place.

## Prémisses différées / vigilances

- **Format audio voice-forge** (PCM ? sample_rate ?) — bloque le fix TTS, à vérifier
  en premier (`voice-forge/app/routes/`).
- **`OpenAISTTService`** peut avoir la même rigidité OpenAI que le TTS — non testé.
- **getUserMedia dans WebView2** : a fonctionné (la coquille capte le micro) mais à
  reconfirmer après le fix TTS (test vocal complet jamais bouclé).
- **Coquille = placeholder logo** ; pastille = stub visuel (pas de RTVI réel).
- Héritées : vraie voix non enrôlée (B2) ; `_RealQwen3TTSEngine` jamais exécuté ;
  8 types d'ontologie jamais vus par l'extraction réelle.

## Méthode (inchangée — CLAUDE.md)

Analyser → proposer → attendre validation → TDD → doc. Tout en français. Jamais de
`git commit` par l'agent ; « texte du commit » = commande git complète (add + commit),
**sans** `Co-Authored-By`. Gros téléchargements lancés par l'utilisateur.

## Suggested skills

- `/impasses` — **en ouverture** : lire le registre (media résolue, blocage TTS).
- `/premisses` — vérifier le format de sortie voice-forge avant de coder le fix TTS.
- `/tdd` — la sous-classe TTS (test factice de la logique de voix passée telle quelle).
- `/delegate` — si un gros lot UI arrive (console à onglets A4, modules forges) ;
  **évaluer d'abord** (le fix TTS est petit et contextuel : inline).
- `/handoff` — générer le 0015 en fin de prochaine session.
