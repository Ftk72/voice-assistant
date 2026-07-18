# World Forge

Accès au monde extérieur pour l'assistant vocal (phase 6, ADR 0007 — souveraineté,
pas isolement) : le LLM reste local, seules des requêtes anonymes sortent.

## Capacités (outils MCP, consommés par le Dialogue Forge)

- `web_search` — extraits du méta-moteur (SearXNG auto-hébergé) ; le LLM en fait
  une **réponse sourcée** (jamais de liste de liens, cf. CONTEXT.md).
- `weather` — prévisions Open-Meteo (API anonyme, sans clé), descriptions WMO en français.
- `briefing` — dernières entrées des flux RSS/Atom configurés (`WORLD_FORGE_FEEDS`).
- `read_page` — texte lisible d'une page désignée (extraction stdlib, tronqué à
  `WORLD_FORGE_PAGE_MAX_CHARS`).

Endpoints directs pour smoke-test : `/health`, `/search?q=`, `/weather?place=`.
MCP : `http://world:8300/mcp` depuis le réseau Docker.

## Passerelles

- `fake` (défaut) — données en dur, zéro réseau : tests et dev hors connexion.
- `real` (`WORLD_FORGE_GATEWAY=real`) — httpx vers SearXNG/Open-Meteo/flux.
  **Jamais exécutée à ce jour** : à valider au premier lancement réel.

## Dev

```bash
uv sync
uv run pytest
uv run ruff check .
```
