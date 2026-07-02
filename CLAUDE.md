# CLAUDE.md — Assistant vocal local

Assistant vocal 100 % souverain (ADR 0007) : OpenWebUI + llama.cpp (LLM, STT) +
services FastAPI sur mesure (« forges »). **Tout est en français** : code
(docstrings, commentaires, messages), tests (`test_le_minuteur_annonce_a_l_echeance`),
docs, commits.

## Lire avant de coder

- `CONTEXT.md` — le glossaire fait foi pour le vocabulaire du domaine.
- `docs/adr/` — décisions actées ; ne pas les rediscuter sans nouveau grilling.
- `docs/handoffs/` — seul le plus récent fait foi ; en générer un via `/handoff`
  en fin de session.
- Clone lecture seule d'OpenWebUI v0.10.2 : `/home/ftk/openwebui/` — vérifier
  dedans plutôt que de mémoire.

## Méthode de travail

- Analyser → proposer → **attendre validation** → coder en TDD → tests → doc.
- **Zéro fork OpenWebUI** (ADR 0003) : uniquement ses mécanismes natifs
  (Filter, MCP, API compatibles OpenAI — dialecte exact).
- **Jamais de `git commit`** : l'utilisateur commite lui-même.
- **Connexion lente** : aucun téléchargement lourd (> 100 Mo) sans accord
  explicite ; petites dépendances PyPI via uv OK (cache local).
- Implémentations volumineuses : déléguer via `/delegate` (haiku→sonnet→opus),
  vérification finale par l'agent principal.

## Conventions des forges (voice-forge, memory-forge, world-forge, time-forge, host-bridge)

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
  (`uv sync --extra chatterbox|graphiti`).
- Modèle à imiter pour un nouveau composant : `memory-forge/`.

## État particulier

La stack n'a **jamais tourné en réel** (modèles non téléchargés — voir
« Reste à faire » du README racine et le dernier handoff). Les adaptateurs
réels (GraphitiMemory, RealWorld, HostBridgeAnnouncer, _RealChatterboxEngine…)
sont écrits mais non validés : ne pas les présenter comme fonctionnels.
