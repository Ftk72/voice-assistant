# Assistant vocal local

Assistant vocal 100 % local et **souverain** (français, voix clonées) : les
modèles (LLM, STT, TTS) et les données personnelles (mémoire, conversations,
agenda) restent sur la machine ; aucun service d'IA cloud (ADR 0007). Seules des
requêtes anonymes (météo, recherche web) sortent.

Depuis l'**ADR 0009** (sortie d'OpenWebUI, 2026-07-07), l'assistant est une
**architecture modulaire** : chaque responsabilité vit dans son propre composant,
et une **coquille** de bureau native assemble le tout. Le vocabulaire du domaine
(Conversation, Orchestrateur de dialogue, Transport voix, Coquille, Module
d'interface, Mot d'éveil…) est défini dans [CONTEXT.md](CONTEXT.md) — **il fait
foi** ; ce README et ce glossaire suffisent à comprendre la stack.

## Architecture

```
┌── natif Windows ──────────────────────────────────────────────────────┐
│                                                                        │
│  Coquille (Tauri v2, Rust + WebView2)        ADR 0010                  │
│   ├─ Console : onglets, chaque onglet = un Module d'interface          │
│   │            servi par son forge (dialogue, mémoire, voix, agenda)   │
│   ├─ Pastille : présence permanente (veille / écoute / parle)          │
│   └─ Carte son : micro + haut-parleurs, audio de conversation en       │
│                  WebRTC (getUserMedia dans WebView2, AEC/NS/AGC Chrome) │
│         │ WebRTC (localhost, pas de TURN)                              │
│         ▼                                                               │
│  Transport voix (Pipecat)                    ADR 0012 · port 8700      │
│   VAD, tours de parole, interruption, mot d'éveil (à venir),           │
│   streaming STT/TTS. Aucune logique métier : il transporte la parole   │
│   entre la coquille, les moteurs et l'Orchestrateur de dialogue.       │
└────────────────────────────────────────────────────────────────────────┘
      │ REST/NDJSON              │ /v1/audio/transcriptions   │ /audio/speech
      ▼                         ▼                            ▼
┌── Docker (docker-compose.yml, ports liés à 127.0.0.1 pour debug) ─────┐
│                                                                        │
│  dialogue (Dialogue Forge, 8600) ── le « cerveau »                     │
│   historique, injection/extraction mémoire, routage des outils (MCP),  │
│   personas (prompt + voix), flux LLM phrase par phrase                 │
│      │ LLM          │ mémoire        │ outils MCP                       │
│      ▼              ▼                ▼                                  │
│  llm            memory (8200)     time (8400) · world (8300)           │
│  llama.cpp      Memory Forge      Time Forge  · World Forge            │
│  Qwen3.6-35B    graphe Graphiti   agenda,       recherche sourcée,     │
│  (~6 Go VRAM)   /Neo4j (+embedder minuteurs,    météo, briefing,       │
│                 Qwen3-Embedding)  annonceur     lecture de page        │
│                 module /viz (3D)                                       │
│                                                                        │
│  stt            voice-forge (8100)                                     │
│  whisper.cpp    TTS Chatterbox, clonage de voix                        │
│  large-v3-turbo module /admin (import, aperçu, suppression des voix)   │
└────────────────────────────────────────────────────────────────────────┘
      │ wav prêt à jouer / actions du catalogue
      ▼
┌── natif Windows, hors Docker (ADR 0008) ──────────────────────────────┐
│  host-bridge (Pont hôte, 8500) — sans intelligence :                   │
│   joue les annonces sur les enceintes, exécute les actions de la       │
│   liste blanche catalog.toml (jamais une commande arbitraire)          │
└────────────────────────────────────────────────────────────────────────┘
```

Trois composants tournent **en natif Windows** (hors Docker) : la **coquille**
(carte son + interface), le **transport voix** (Pipecat, l'audio de conversation
ne traverse plus jamais WSL), et le **Pont hôte** (annonces sur enceintes,
actions). Tout le reste est conteneurisé.

Décisions techniques : [docs/adr/](docs/adr/) · Glossaire (fait foi) :
[CONTEXT.md](CONTEXT.md) · Roadmap : [docs/roadmap.md](docs/roadmap.md) ·
Critères de recette : [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md).

## État de la reconstruction

L'ancienne stack (OpenWebUI unique interface) a été **validée de bout en bout le
2026-07-07** puis abandonnée par l'ADR 0009 (big bang assumé : l'assistant est
muet pendant la reconstruction). La nouvelle stack se rebâtit maillon par
maillon ; au 2026-07-16, la chaîne voix est débuggée et le **premier tour de
parole passe dans la coquille** (accueil TTS audible, STT français, réponse du
Dialogue Forge). Les mesures de l'ancienne stack servent de **références
historiques** (voir [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)).

## Lancer

### 1. Les forges (Docker, dans WSL2)

1. **Télécharger les modèles** (une seule fois, connexion rapide requise —
   l'utilisateur lance) : `./scripts/download-models.sh` (vérifier les dépôts
   Hugging Face indiqués dans le script). Modèles : LLM Qwen3.6-35B-A3B, STT
   whisper large-v3-turbo, embedder Qwen3-Embedding-0.6B, poids Chatterbox.
2. **Renseigner `.env`** (non versionné) : `NEO4J_PASSWORD`, `SEARXNG_SECRET`,
   `HOST_BRIDGE_TOKEN`.
3. **Construire et lancer** : `docker compose up -d --build`
   (le build de voice-forge tire torch/torchaudio, ~2,5 Go).
4. **Vérifier** : `docker compose ps` (tous *healthy*). Ports de debug (liés à
   `127.0.0.1`) : dialogue 8600, memory 8200 (`/viz`), voice-forge 8100
   (`/admin`), world 8300, time 8400, Neo4j Browser 7474.

### 2. Le Pont hôte (hors Docker, sur l'hôte)

Les annonces sur enceintes et les actions passent par lui (ADR 0008) —
`scripts/demarrage-hote.sh` le lance et répare les montages après un reboot
Windows. Détails : [host-bridge/README.md](host-bridge/README.md).

### 3. Le transport voix (natif Windows)

Pipecat tourne en natif sur Windows (port 8700) pour que l'audio de conversation
ne traverse pas WSL. Extra lourd optionnel, lancé par l'utilisateur :
`uv sync --extra pipecat`. Détails : [transport-voix/README.md](transport-voix/README.md).

### 4. La coquille (natif Windows)

Application Tauri v2 (Rust + WebView2), à compiler **sur Windows** (jamais dans
WSL : `cargo` y produirait une app Linux) : `cargo tauri dev`. Elle est la carte
son et assemble les modules d'interface. Détails et prérequis :
[coquille/README.md](coquille/README.md).

## Ajouter une voix

- Déposer un dossier `voices/MaVoix/` contenant un `speaker.wav` de quelques
  secondes, **ou** passer par le module d'interface `/admin` de voice-forge
  (`http://127.0.0.1:8100/admin` — import, aperçu, suppression). La voix
  apparaît sans redémarrage.
- Optionnel : un `config.json` à côté du `speaker.wav` surcharge les paramètres
  (`language`, `exaggeration`, `cfg_weight`).
- Un persona associe un prompt « voice-first » à une voix par défaut (voir
  [personas/](personas/)) ; la voix est dérogeable en cours de conversation sans
  changer de persona (CONTEXT.md § Persona).

## Presets audio

Deux réglages d'usage (CONTEXT.md § Preset audio), basculables en un clic :
**casque** (interruption de l'assistant activée) et **haut-parleurs**
(interruption désactivée, pour éviter que l'assistant ne s'entende et se coupe).

## Les composants

| Composant | Rôle | Détails |
| --- | --- | --- |
| Coquille (Tauri) | Carte son + assemblage des modules d'interface | [coquille/](coquille/) |
| Transport voix (Pipecat) | Temps réel : VAD, tours, interruption, mot d'éveil | [transport-voix/](transport-voix/) |
| Dialogue Forge | Le cerveau : historique, mémoire, outils, personas | `dialogue-forge/` |
| voice-forge | TTS + clonage de voix (module `/admin`) | [voice-forge/](voice-forge/) |
| memory-forge | Mémoire en graphe (Graphiti/Neo4j, module `/viz`) | [memory-forge/](memory-forge/) |
| time-forge | Agenda, minuteurs, annonceur | [time-forge/](time-forge/) |
| world-forge | Recherche sourcée, météo, briefing, lecture de page | [world-forge/](world-forge/) |
| Pont hôte | Annonces sur enceintes + actions du catalogue (hors Docker) | [host-bridge/](host-bridge/) |
| llama.cpp | LLM (Qwen3.6-35B-A3B) | service `llm` |
| whisper.cpp | STT (large-v3-turbo, français) | service `stt` |

## Éthique et sécurité

- Voix clonées de personnes réelles : usage strictement personnel, aucune
  diffusion des sorties audio.
- Ports Docker liés à `127.0.0.1` (debug uniquement) ; la coquille consomme les
  forges en HTTP local. Le Pont hôte écoute `0.0.0.0` en usage réel, derrière un
  pare-feu limité au réseau Docker et protégé par un jeton partagé.
- Aucun appel réseau sortant à l'exécution hors requêtes anonymes du World Forge
  (souveraineté, ADR 0007).

## Développement

Chaque forge suit le même patron (ports/adaptateurs, ADR 0009, modèle
memory-forge) : `uv sync` puis `uv run pytest` et `uv run ruff check .` — tout
tourne sans GPU ni Neo4j grâce aux adaptateurs factices par défaut.
