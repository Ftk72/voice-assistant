# Dialogue Forge

L'**orchestrateur de dialogue** de l'assistant vocal (ADR 0009) : le cerveau
conversationnel. Il tient l'historique, **injecte** la mémoire avant chaque tour
et fait **extraire** l'épisode après, route les appels d'**outils** vers les
forges (client MCP), applique le **persona** et diffuse la réponse du LLM
**phrase par phrase** (le TTS en aval synthétise phrase par phrase).

Composant en **texte seul**, testable au `curl` sans audio. Il n'a aucune
interface (la coquille l'affiche) et — écart assumé aux autres forges — il est
*client* MCP, il n'expose **aucun serveur MCP**.

## Lancement local

```bash
cd dialogue-forge
uv sync
uv run python -m app        # écoute sur http://127.0.0.1:8600
uv run pytest
uv run ruff check .
```

Par défaut, les trois adaptateurs sont **factices** (zéro réseau) : le forge
répond « D'accord. » sans LLM, mémoire ni outils réels. On bascule vers les
adaptateurs réels par variables d'environnement (voir plus bas).

## Endpoints

`GET /health`

```bash
curl http://127.0.0.1:8600/health
# {"status":"ok"}
```

`GET /personas` — les personas chargés (nom, voix) :

```bash
curl http://127.0.0.1:8600/personas
# [{"nom":"Assistant","voix":"Emma"},{"nom":"Batman","voix":"Batman"}]
```

`POST /conversations` — ouvre un fil (persona optionnel, défaut `assistant`) :

```bash
curl -X POST http://127.0.0.1:8600/conversations \
  -H 'content-type: application/json' -d '{"persona": "batman"}'
# {"id":"<identifiant>"}
```

`GET /conversations/{id}` — l'historique du fil (404 si inconnu).

`POST /conversations/{id}/tours` — joue un tour ; réponse **NDJSON** streamée,
une ligne `phrase` par phrase puis une ligne `fin` avec le texte complet :

```bash
curl -N -X POST http://127.0.0.1:8600/conversations/<identifiant>/tours \
  -H 'content-type: application/json' -d '{"texte": "Bonjour, quel temps fait-il ?"}'
# {"type":"phrase","texte":"Bonjour toi."}
# {"type":"phrase","texte":"Comment vas-tu ?"}
# {"type":"fin","reponse":"Bonjour toi. Comment vas-tu ?"}
```

## Variables d'environnement (`env_prefix = DIALOGUE_FORGE_`)

| Variable | Défaut | Rôle |
| --- | --- | --- |
| `DIALOGUE_FORGE_HOST` | `127.0.0.1` | Adresse d'écoute |
| `DIALOGUE_FORGE_PORT` | `8600` | Port d'écoute |
| `DIALOGUE_FORGE_LLM_BACKEND` | `fake` | `fake` ou `openai` (llama.cpp) |
| `DIALOGUE_FORGE_LLM_BASE_URL` | `http://127.0.0.1:8001/v1` | API compatible OpenAI |
| `DIALOGUE_FORGE_LLM_MODEL` | `local` | Nom de modèle |
| `DIALOGUE_FORGE_MEMOIRE_BACKEND` | `fake` | `fake` ou `rest` (memory-forge) |
| `DIALOGUE_FORGE_MEMORY_FORGE_URL` | `http://127.0.0.1:8200` | Base URL memory-forge |
| `DIALOGUE_FORGE_OUTILS_BACKEND` | `fake` | `fake` ou `mcp` |
| `DIALOGUE_FORGE_MCP_URLS` | time/world/memory | Serveurs MCP agrégés (JSON) |
| `DIALOGUE_FORGE_PERSONAS_DIR` | `../personas` | Dossier des personas |
| `DIALOGUE_FORGE_PERSONA_DEFAUT` | `assistant` | Persona par défaut |
| `DIALOGUE_FORGE_MAX_ITERATIONS_OUTILS` | `5` | Bornage de la boucle d'outils |

## Adaptateurs réels — validés en réel le 2026-07-07

Les trois adaptateurs réels ont été **validés en réel le 2026-07-07** contre la
stack Docker (llama.cpp, memory-forge, time-forge, world-forge) : tour simple,
tour avec outil (météo via world-forge), tour mémoire, multi-tours et
extraction d'épisode ont tous fonctionné du premier coup, sans correctif
nécessaire. Ils restent hors du filet de tests automatisés (les tests
n'utilisent que les factices, zéro réseau) :

- `app/llm/openai_compat.py` — streaming vers l'API chat/completions de llama.cpp ;
- `app/memoire/rest.py` — REST vers memory-forge (`GET /search`, `POST /episodes`) ;
- `app/outils/mcp.py` — client MCP streamable HTTP agrégeant time-, world- et memory-forge.

Point d'attention observé lors de l'essai (**corrigé** depuis, voir ci-dessous) :
la latence de première phrase dès qu'un tour inclut la liste des outils MCP
dans la requête LLM grimpait à plusieurs secondes (jusqu'à ~8 s observés),
contre ~0,9 s de référence sans outils sur l'ancienne stack.

## Cache de préfixe LLM — préfixe stable d'un tour à l'autre

Diagnostic : llama.cpp (Qwen3.6 MoE, un seul slot) réutilise le cache du tour
précédent **si le préfixe du prompt est identique octet pour octet**. L'ancien
code (1) rappelait `lister_outils()` à chaque tour et (2) injectait les faits
mémoire **dans le message système** : le préfixe changeait à chaque tour, le
cache était invalidé, chaque tour repayait le prefill complet.

Correctif : les outils sont listés **une seule fois** au démarrage
(`Orchestrateur.definir_outils`, appelé depuis le lifespan de `app/main.py`) ;
le message système ne contient plus que le prompt du persona, constant d'un
tour à l'autre ; les faits mémoire sont injectés **en aval**, dans un message
`user` de contexte (`[Contexte mémoire — …]`) inséré juste avant le message
utilisateur du tour et **persisté** dans l'historique — ce message varie,
jamais le système.

Mesuré au banc réel (LLM réel + outils MCP réels + mémoire factice avec faits
programmés, persona dédiée pour garantir un premier tour réellement à froid),
latence de la première ligne NDJSON sur 3 tours consécutifs d'une même
conversation :

| Tour | Latence 1ère ligne NDJSON | Tokens de prompt réellement retraités (logs `voice-assistant-llm-1`) |
| --- | --- | --- |
| 1 (à froid) | 5,46 s | 1195 / 1539 (préfixe jamais vu) |
| 2 | 1,22 s | 82 / 1620 (`f_keep` = 0,990) |
| 3 | 1,21 s | 99 / 1684 (`f_keep` = 0,979) |

Les tours suivants ne retraitent plus que les quelques dizaines de tokens du
nouveau tour (message de contexte éventuel + tour utilisateur + réponse
précédente), au lieu de l'intégralité du contexte (~1,2-1,7 k tokens) : c'est
la preuve, au niveau du serveur LLM, que le préfixe reste stable. Le premier
tour à froid (5,46 s) est plus élevé que la référence de diagnostic (3 s) —
persona nonce inédite + outils MCP réels au banc, pas de régression : c'est le
tour à froid, payé une fois par conversation.

## Deux limites corrigées — boucle d'outils persistée et recall halluciné

Deux limites connues ont été traitées en TDD sur la base du correctif de
cache ci-dessus.

**Lot 1 — persistance des messages de la boucle d'outils.** Avant correctif,
`jouer_tour` ne persistait dans `historique` que le tour utilisateur et la
réponse finale : les messages intermédiaires de la boucle d'outils (`assistant`
avec `tool_calls`, résultats `role: "tool"`) étaient perdus, ce qui invalidait
partiellement le cache au tour suivant (le préfixe envoyé au LLM divergeait du
préfixe déjà vu) et faisait perdre au LLM la trace de ce que ses outils avaient
répondu. Correctif : `Orchestrateur.jouer_tour` persiste désormais, dans
l'ordre exact où ils ont été envoyés au LLM, tous les messages de la boucle
d'outils avant le message assistant final. La capture d'épisode (texte
utilisateur + réponse finale) est inchangée.

**Lot 2 — consigne d'outils constante (le recall halluciné).** Bug observé en
réel : sur « Qu'est-ce que je t'ai dit sur mes projets ? », le LLM pouvait ne
pas appeler l'outil `recall` (MCP memory-forge) et inventer un souvenir.
Correctif : `_construire_systeme` ajoute au prompt du persona un bloc de
consignes **constant** (`CONSIGNES_OUTILS`, constante de module), séparé par
une ligne vide — cadrant l'usage de `recall` (toujours l'appeler pour toute
référence à une conversation passée, ne jamais inventer un souvenir) et des
outils du monde réel en général. Le bloc est identique octet pour octet d'un
tour et d'un persona à l'autre : le cache de préfixe reste intact.

### Validation au banc réel (LLM + outils MCP réels, mémoire factice)

Scénario joué dans une même conversation (persona nonce, `DIALOGUE_FORGE_MEMOIRE_BACKEND`
laissé à `fake` pour l'injection amont — seule la lecture via l'outil `recall`
touche le vrai memory-forge, aucune écriture n'a pollué le graphe) :

1. « Qu'est-ce que je t'ai dit sur mes projets ? » — `recall` a bien été appelé
   (un seul `CallToolRequest` dans `docker logs voice-assistant-memory-1`,
   avec l'appel embeddings associé) et la réponse s'appuie sur un fait réel du
   graphe (« L'Utilisateur souhaite lancer le projet professionnel d'ici la fin
   de l'année 2026. », confirmé via `GET /search?q=projets` sur memory-forge) —
   pas une hallucination. Premier essai de formulation du bloc de consignes
   suffisant, aucune itération nécessaire.
2. « Quel temps fait-il à Paris ? » — l'outil `weather` a bien été appelé
   (`CallToolRequest` + requêtes `open-meteo.com` dans `docker logs
   voice-assistant-world-1`), réponse cohérente.
3. « Merci, redis-moi ça en un mot. » — réponse « Nuageux. » en **2,01 s**
   pour la première ligne NDJSON. Légèrement au-dessus de la cible (1-1,5 s) ;
   diagnostic via les logs `voice-assistant-llm-1` : `f_keep = 0,946`, seuls
   161 tokens sur 2376 retraités — le cache reste très majoritairement
   réutilisé (lot 1 tient sa promesse), l'écart vient du contexte plus long
   qu'au banc précédent (les messages de la boucle d'outils des deux tours
   précédents sont désormais persistés, comme voulu) et du débit de prefill
   propre aux experts MoE en RAM CPU, pas d'une régression de cache.

Tous les processus lancés pour ce banc ont été arrêtés en fin de mesure ; le
script de banc vit dans le scratchpad (hors dépôt).
