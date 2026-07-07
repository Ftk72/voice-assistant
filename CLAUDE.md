# CLAUDE.md — Assistant vocal local

Assistant vocal 100 % souverain (ADR 0007) en **refonte modulaire** (ADR 0009,
2026-07-07) : Dialogue Forge (cerveau), Pipecat (transport voix), coquille
Tauri (interface + carte son), llama.cpp (LLM), whisper.cpp (STT), forges
FastAPI sur mesure. OpenWebUI est **abandonné** (big bang assumé : l'assistant
est muet pendant la reconstruction). **Tout est en français** : code
(docstrings, commentaires, messages), tests (`test_le_minuteur_annonce_a_l_echeance`),
docs, commits.

## Lire avant de coder

- `CONTEXT.md` — le glossaire fait foi pour le vocabulaire du domaine
  (réécrit à l'ADR 0009 : Conversation, Orchestrateur de dialogue, Transport
  voix, Coquille, Module d'interface, Mot d'éveil).
- `docs/adr/` — décisions actées ; ne pas les rediscuter sans nouveau grilling.
  L'ADR 0009 (sortie d'OpenWebUI) prime sur toute mention d'OpenWebUI restée
  dans les documents plus anciens (README, ACCEPTANCE, plan-de-tests…).
- `docs/handoffs/` — seul le plus récent fait foi ; en générer un via `/handoff`
  en fin de session.

## Méthode de travail

- Analyser → proposer → **attendre validation** → coder en TDD → tests → doc.
- **Jamais de `git commit`** : l'utilisateur commite lui-même.
- **Connexion lente** : aucun téléchargement lourd (> 100 Mo) sans accord
  explicite — et c'est **l'utilisateur qui lance** les gros téléchargements
  (fournir les commandes, dépôts/tags vérifiés via API avant de les donner) ;
  petites dépendances PyPI via uv OK (cache local).
- Implémentations volumineuses : déléguer via `/delegate` (haiku→sonnet→opus),
  vérification finale par l'agent principal.
- Avant toute tâche significative : audit des prémisses (`/premisses`) — les
  croyances des handoffs se vérifient, ne se croient pas.
- Toute piste morte se capture à chaud dans `docs/impasses.md` (`/impasses`) ;
  consulter ce registre avant tout diagnostic.

## Conventions des forges (dialogue-forge à naître, voice-forge, memory-forge, world-forge, time-forge, host-bridge)

- Python 3.12, uv ; `uv sync` puis `uv run pytest` et `uv run ruff check .`
  dans chaque composant — tout doit rester vert.
- Ruff : line-length 100, select `["E","F","I","UP","B","SIM"]` ;
  pytest : `asyncio_mode = "auto"`, `pythonpath = ["."]`.
- **Ports/adaptateurs** : un port ABC (`app/.../base.py`) + un adaptateur
  factice (défaut, zéro réseau/matériel, utilisé par les tests) + un adaptateur
  réel documenté « jamais exécuté à ce jour » tant qu'il n'a pas tourné.
  Factories dans `app/main.py`, sélection par `Settings` (pydantic-settings,
  `env_prefix` par composant).
- FastAPI : `create_app(settings)` + lifespan, `/health` → `{"status":"ok"}`,
  MCP via `FastMCP(..., stateless_http=True, streamable_http_path="/")` monté
  sur `/mcp`. Descriptions d'outils MCP orientées voix (« restitue oralement,
  ne lis pas la liste »).
- Dépendances lourdes optionnelles dans un extra séparé
  (`uv sync --extra chatterbox|qwen3tts|graphiti`) ; extras aux épinglages
  inconciliables déclarés conflictuels (`[tool.uv] conflicts`, cf. voice-forge).
- **Module d'interface** : chaque forge sert sa propre UI (pattern
  voice-forge `/admin`, memory-forge `/viz`) ; la coquille Tauri ne fait
  qu'assembler — jamais de logique métier côté coquille.
- Modèle à imiter pour un nouveau composant : `memory-forge/`.

## Plateforme (pièges permanents — le détail vit dans docs/impasses.md)

- **RTX 5080 = Blackwell sm_120** : aucun binaire CUDA ne se présume
  compatible avant un test réel (torch < 2.8, images officielles whisper.cpp
  et consorts en sont morts). Compilations Docker : toujours borner `-j`.
- **WSL2 + Docker Desktop** : après un reboot Windows, montages possiblement
  vides et Pont hôte arrêté — `scripts/demarrage-hote.sh` répare ; après toute
  manip GPU, **redémarrer le LLM en dernier** (sinon poids paginés en RAM
  partagée, débit divisé par 10).
- L'audio de **conversation** passe par la coquille (natif Windows, WebRTC) ;
  seules les **annonces** transitent par le Pont hôte (aplay/WSLg).

## État particulier

L'ancienne stack (OpenWebUI) a été **validée de bout en bout le 2026-07-07**
(voix, mémoire, annonces sur enceintes) puis abandonnée par l'ADR 0009 : ses
mesures servent de référence (latence voix→voix 2,88 s, STT 0,15-0,5 s,
TTS ~2 s, LLM ~33 tok/s). La nouvelle stack (Dialogue Forge, Pipecat, coquille)
n'existe pas encore. Adaptateurs réels jamais exécutés à ce jour :
`SubprocessRunner` (host-bridge) et `_RealQwen3TTSEngine` (voice-forge) — ne
pas les présenter comme fonctionnels.
