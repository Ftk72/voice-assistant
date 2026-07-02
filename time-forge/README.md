# Time Forge

Le temps de l'assistant vocal (phases 3+5) : **agenda** local (le lieu unique des
choses datées — un rappel est un événement dont l'annonce est la raison d'être,
cf. CONTEXT.md), **minuteurs** éphémères précis à la seconde, et **annonceur**
(le seul canal de parole spontanée).

## Outils MCP (consommés par OpenWebUI)

- `create_event` — événement / rappel (`announce_lead_minutes=0`) / rendez-vous
  avec préavis (`announce_lead_minutes=60`).
- `list_events`, `delete_event` — consultation et suppression à la voix.
- `set_timer`, `cancel_timer`, `list_timers` — « mets un minuteur pâtes de 8 minutes ».

Endpoints directs pour smoke-test : `/health`, `/events`, `/timers`,
`POST /announce {"text": …}` (teste la chaîne annonceur sans attendre une échéance).
MCP : `http://time:8400/mcp` depuis le réseau Docker.

## Architecture

- **Store** : `memory` (défaut, tests) ou `sqlite` (`TIME_FORGE_STORE=sqlite`,
  stdlib, volume Docker) — l'agenda survit aux redémarrages.
- **Minuteurs** : tâches asyncio, pas de persistance (un redémarrage les perd —
  assumé pour un compte à rebours de cuisine).
- **Annonceur** : `log` (défaut, tests) ou `hostbridge`
  (`TIME_FORGE_ANNOUNCER=hostbridge`) : synthèse via le Voice Forge puis envoi
  du wav au Pont hôte qui le joue sur les enceintes (ADR 0008).
  **Jamais exécuté à ce jour** : à valider au premier lancement réel.
- La notification visuelle dans OpenWebUI (glossaire : l'annonce est « doublée
  d'une notification visuelle ») n'est pas encore branchée — à traiter au
  réglage réel, via les mécanismes natifs d'OpenWebUI.

Le conteneur doit avoir `TZ` (ex. `Europe/Paris`) : les échéances sont en heure locale.

## Dev

```bash
uv sync
uv run pytest
uv run ruff check .
```
