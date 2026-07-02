# Assistant vocal local

Assistant vocal 100 % local (français, voix clonées) avec **OpenWebUI comme unique interface**. Zéro fork, zéro modification d'OpenWebUI : tout passe par ses mécanismes natifs.

```
┌─────────────────────────── Docker ────────────────────────────┐
│                                                               │
│  openwebui (UI, seule exposée : http://127.0.0.1:3000)        │
│     │ chat        │ voix→texte        │ texte→voix            │
│     ▼             ▼                   ▼                       │
│  llm          stt                voice-forge                  │
│  llama.cpp    llama.cpp          FastAPI + Chatterbox         │
│  Qwen3.6-35B  Voxtral Mini       clonage de voix (~3 Go VRAM) │
│  (~6 Go VRAM) (~3 Go VRAM)       admin : 127.0.0.1:8100/admin │
└───────────────────────────────────────────────────────────────┘
```

Décisions techniques : [docs/adr/](docs/adr/) · Glossaire : [CONTEXT.md](CONTEXT.md) · Critères d'acceptation : [docs/ACCEPTANCE.md](docs/ACCEPTANCE.md)

## Installation

1. **Télécharger les modèles** (~26 Go, une seule fois) : `./scripts/download-models.sh`
   (vérifier les noms de dépôts Hugging Face indiqués dans le script).
2. **Construire et lancer** : `docker compose up -d --build`
   (le build du Voice Forge télécharge torch/torchaudio, ~2,5 Go).
3. **Ouvrir** http://127.0.0.1:3000 — la config audio (STT/TTS) est injectée au premier démarrage ; détails et personas : [docs/OPENWEBUI.md](docs/OPENWEBUI.md), [personas/](personas/).

## Ajouter une voix

- Déposer un dossier `voices/MaVoix/` contenant un `speaker.wav` de quelques secondes, **ou** passer par la mini-page d'admin http://127.0.0.1:8100/admin (import, aperçu, suppression).
- La voix apparaît immédiatement dans OpenWebUI (Settings → Audio et éditeur de persona), sans redémarrage.
- Optionnel : un `config.json` à côté du `speaker.wav` surcharge les paramètres (`language`, `exaggeration`, `cfg_weight`).

## Presets audio

- **Casque** : Settings → Audio → activer *Allow Voice Interruption in Call*.
- **Haut-parleurs** : désactiver ce réglage (sinon l'assistant s'entend et s'interrompt).

## Mémoire persistante (Memory Forge)

Second composant sur mesure : mémoire en graphe (Graphiti/Neo4j, ADR 0005) alimentée par les conversations (Filter OpenWebUI) et par les documents. Recall/oubli via MCP. Détails : [memory-forge/README.md](memory-forge/README.md), critères : [docs/ACCEPTANCE-MEMOIRE.md](docs/ACCEPTANCE-MEMOIRE.md).

- **Déposer un document** : glisser un `.md` ou `.pdf` dans [documents/](documents/) — ingéré automatiquement (~10 s), relié aux souvenirs par les entités communes (ADR 0006).
- **Visualiser le graphe** : mini-page du Memory Forge sur http://127.0.0.1:8200/viz (recherche d'entité, voisinage, filtres provenance/validité) ; Neo4j Browser sur http://127.0.0.1:7474 pour le Cypher brut.

## Monde extérieur (World Forge)

Accès sourcé au web (phase 6, ADR 0007 — souveraineté, pas isolement) : le LLM reste local, seules des requêtes anonymes sortent. Outils MCP `web_search` (réponse sourcée via SearXNG auto-hébergé), `weather` (Open-Meteo), `briefing` (flux RSS), `read_page`. Détails : [world-forge/README.md](world-forge/README.md).

## Quotidien et agenda (Time Forge)

Le temps de l'assistant (phases 3+5, ADR 0008) : agenda local (SQLite souverain), rappels, minuteurs précis à la seconde, et l'annonceur — le canal de parole spontanée. Outils MCP pour créer/lister/supprimer événements et minuteurs. À l'échéance, l'annonce est synthétisée par le Voice Forge puis jouée sur les enceintes via le Pont hôte. Détails : [time-forge/README.md](time-forge/README.md).

## Pont hôte (host-bridge)

Le seul composant **hors Docker** (ADR 0008) : le pied de l'assistant sur la machine hôte, sans intelligence. Il joue les annonces reçues sur les enceintes et exécute les actions de la liste blanche `catalog.toml` — jamais une commande arbitraire. Les conteneurs ne peuvent ni parler sur les enceintes ni agir sur le bureau ; le Pont, lui, tourne sur l'hôte et est joignable via `http://host.docker.internal:8500`. Lancement : `uv run python -m app` dans [host-bridge/](host-bridge/) (voir son README).

## Éthique et sécurité

- Voix clonées de personnes réelles : usage strictement personnel, aucune diffusion des sorties audio.
- Seul OpenWebUI est publié ; LLM, STT et Voice Forge sont liés à `127.0.0.1`.
- Aucun appel réseau sortant à l'exécution (hors téléchargement initial).

## Développement

Voir [voice-forge/README.md](voice-forge/README.md) et [memory-forge/README.md](memory-forge/README.md) — `uv run pytest` dans chaque dossier (sans GPU ni Neo4j grâce aux backends factices).

## Reste à faire (jour de bonne connexion)

1. `./scripts/download-models.sh` (vérifier les dépôts HF, dont bge-m3) puis `docker compose up -d --build`.
2. Valider la config Audio dans OpenWebUI, créer les personas, installer la Filter mémoire et brancher le serveur MCP `http://memory:8200/mcp` ([docs/OPENWEBUI.md](docs/OPENWEBUI.md)).
3. **Mesurer la latence** fin de parole → début de réponse (cible ≤ 2 s, docs/ACCEPTANCE.md) et le surcoût d'injection mémoire (≤ 300 ms, docs/ACCEPTANCE-MEMOIRE.md).
4. Vérifier les API réelles jamais exécutées : `chatterbox-tts` (`_RealChatterboxEngine`) et `graphiti-core` (`GraphitiMemory`, `uv sync --extra graphiti`).
5. **Monde extérieur** : puller l'image `searxng/searxng` et générer un `secret_key` dans `searxng/settings.yml` ; valider la passerelle réelle `RealWorld` (SearXNG/Open-Meteo/flux RSS).
6. **Quotidien + Pont hôte** : lancer le Pont hôte sur l'hôte Windows (`HOST_BRIDGE_HOST=0.0.0.0` + pare-feu limité au réseau Docker), écrire `catalog.toml` depuis `host-bridge/catalog.example.toml`, et valider la chaîne d'annonce réelle `HostBridgeAnnouncer` (Voice Forge → Pont hôte → enceintes).
7. Configurer les serveurs MCP additionnels dans OpenWebUI : `http://world:8300/mcp`, `http://time:8400/mcp`, `http://host.docker.internal:8500/mcp` (voir [docs/ACCEPTANCE-CAPACITES.md](docs/ACCEPTANCE-CAPACITES.md)).
# voice-assistant
