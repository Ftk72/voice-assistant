Action Forge

L'agir de l'assistant vocal, en escalade sur trois paliers (ADR 0013). Palier 1 livré ici : l'**Atelier**, le bac à sable Docker jetable — un par Tâche, borné CPU/RAM/temps, détruit après le Compte rendu. Contrat : `../docs/wayfinder/tickets/0031-contrat-de-l-action-forge.md` · vocabulaire : `../CONTEXT.md` § Agir.

## Lancer (dev, sans Docker)

```bash
uv sync
uv run python -m app        # http://127.0.0.1:8800 — Atelier factice
```

Configuration par variables d'environnement (préfixe `ACTION_FORGE_`) : `ATELIER_BACKEND` (`fake` par défaut, `docker` en production — nécessite `uv sync --extra docker`), `ATELIER_IMAGE` (défaut `action-forge-atelier:latest`), `ATELIER_CPUS`, `ATELIER_MEMOIRE_MO`, `ATELIER_TIMEOUT_SECONDES`, `ECHANGE_DIR_HOTE` (chemin **hôte** du dossier d'échange — le socket Docker fait résoudre les montages par le daemon hôte), `LLM_BACKEND` (`fake` par défaut, `openai` pour llama.cpp), `LLM_BASE_URL` (défaut `http://127.0.0.1:8001/v1`), `LLM_MODEL`, `BUDGET_PAS` (défaut 8 — borne la boucle CodeAct), `HOST` (défaut `127.0.0.1`), `PORT` (défaut `8800`).

## Architecture

`app/atelier/base.py` définit le port `Atelier` (`demarrer`, `executer`, `detruire`), calqué sur le contrat 0031 : un Atelier ne voit jamais le dépôt, les secrets ni le socket Docker — son seul montage est le sous-dossier d'échange de sa Tâche.

- `AtelierFactice` — factice (journalise les Actions, renvoie des résultats préparés, pattern `ExecuteurCypherFactice` de memory-forge) : tests et dev.
- `AtelierDocker` — adaptateur réel (`uv sync --extra docker` + socket Docker monté), au réel depuis le 2026-07-20 (lancement/exécution/destruction d'un conteneur, ticket 0033). Pilote des conteneurs Docker **frères** via le socket — jamais monté dans l'Atelier lui-même.

`app/boucle.py` (`BoucleCodeAct`) orchestre le cycle observe-réfléchit-agit
(ADR 0013, ticket 0034) : à chaque pas, `app/llm/` (port `MoteurLLM`,
`MoteurLLMFactice` pour les tests, `MoteurLLMOpenAI` — llama.cpp, validé en
réel le 2026-07-20) répond soit par une Action (bloc ```bash``` exécuté dans
l'Atelier, résultat réinjecté comme observation), soit par le Compte rendu
final (`TERMINÉ: ...`), le tout borné par `budget_pas`. `app/gestionnaire.py`
tient les Tâches en mémoire (contrat 0031, une Tâche = une tâche asyncio dans
son propre Atelier) et `app/routes.py` les expose en REST asynchrone
(`POST /taches`, `GET /taches`, `GET /taches/{id}`,
`POST /taches/{id}/annulation`, `GET /taches/{id}/flux` en SSE).

## L'image de l'Atelier

`atelier/Dockerfile` — image fixe (contrat 0031), outillée bash/Python 3.12/uv/ffmpeg, sans réseau par défaut. Construite en compose sous le profil `images` (jamais démarrée par un `up` normal) :

```bash
docker compose --profile images build atelier-image
```

## Ce qui n'est pas encore là

Pas de `/mcp` ni d'UI `/atelier` (ticket 0035, « l'action à la voix ») : le palier 1 se pilote pour l'instant en texte pur (`curl`), conformément au ticket 0034.
