# Handoff 0018 — Ticket 0029 tranché au grilling, reste à livrer

> Session du 2026-07-18. Périmètre de la session : ouverture du ticket
> wayfinder 0029 (correction ciblée des extractions), audit des prémisses,
> grilling complet avec l'utilisateur, décisions consignées. **Aucune ligne de
> code écrite** — la prochaine session livre.

## État

- Toutes les décisions du 0029 sont **actées et écrites** dans
  [le ticket](../wayfinder/tickets/0029-correction-ciblee-des-extractions.md)
  (section « Décisions du grilling du 2026-07-18 ») — ne pas les rediscuter,
  les lire là-bas : c'est la source de vérité, ce handoff ne les duplique pas.
- La [carte graphe-mémoire](../wayfinder/carte-graphe-memoire.md) porte le
  résumé d'une ligne (section « Pas encore spécifié »).
- L'utilisateur a donné son **feu vert de principe** sur le récapitulatif du
  grilling juste avant de partir ; la livraison n'a pas commencé.

## Prémisses vérifiées cette session (à ne pas re-payer, mais périssables)

- `ontologie.py` compte **huit** types, pas six (le ticket disait six — corrigé).
- Le type d'entité n'existe **nulle part** dans la chaîne actuelle :
  `NoeudGraphe` (memory-forge/app/schemas.py) n'a pas de champ `type`, le
  corpus synthétique pose `labels: ['Entity']` nu
  (scripts/corpus_synthetique.py), le ticket 0026 (encodage visuel) n'est pas
  livré.
- `GraphEdge` n'expose pas l'`uuid` de l'arête au client — l'invalidation
  ciblée l'exige, à faire remonter dans `/graph/complet`.
- Le panneau latéral de `/viz` (app/viz/index.html, ~ligne 422) porte déjà
  « Oublier cette entité » et la liste des faits — c'est là que les gestes
  s'insèrent.
- Impasse à respecter (docs/impasses.md, 2026-07-18) : toute écriture Cypher
  directe doit préserver les champs obligatoires de Graphiti (le corpus a déjà
  cassé `/search` en les omettant).

## Prochaine étape (ordre suggéré)

1. TDD côté serveur dans memory-forge : plomberie (`type` sur `NoeudGraphe`,
   `uuid` sur `GraphEdge`), quatre méthodes du port `GraphMemory`
   (fake d'abord, Graphiti ensuite), quatre routes `POST /corrections/*`,
   trace `corrige_*`. Détails dans le ticket.
2. Corpus : types posés sur les 264 entités + 3 cas fautifs volontaires, sous
   contrat de test ; réinjection `NEO4J_PASSWORD=… uv run python -m
   scripts.corpus_synthetique` (purger avant usage réel de la mémoire).
3. Panneau `/viz` : sélecteur de type, crayon de renommage, « marquer faux »
   par fait, badge « corrigé à la main », « annuler » sur les manuelles.
4. Rebuild de l'image `memory` puis jugement à l'œil par l'utilisateur au
   navigateur (critère de clôture du ticket).
5. `uv sync`, `uv run pytest`, `uv run ruff check .` verts dans memory-forge ;
   jamais de `git commit` (l'utilisateur commite).

## Points d'attention

- Le renommage réel doit **recalculer `name_embedding`** via l'embedder
  (port 8003) — vérifier comment l'adaptateur Graphiti expose son embedder
  avant de coder ; le fake n'en a évidemment pas besoin.
- L'adaptateur Graphiti tourne au réel depuis les tickets 0016-0021, mais des
  docstrings « jamais exécuté » périmées traînent dans graphiti.py — ne pas
  s'y fier, ne pas non plus les croire sur parole : re-tester.
- La protection contre une ré-extraction est **contractuelle seulement**
  (propriétés `corrige_*` requêtables) — assumé au grilling, pas un trou à
  reboucher maintenant.
- Fusion de doublons et création manuelle de faits : **hors périmètre**, ne
  pas les laisser rentrer par la fenêtre de l'UI.

## Skills suggérés

- `/premisses` en ouverture (re-vérifier les prémisses ci-dessus : elles
  étaient vraies aujourd'hui, pas éternellement).
- `/impasses` avant tout diagnostic Neo4j/corpus.
- `/tdd` pour la livraison serveur ; `/delegate` si la livraison paraît
  volumineuse (le panneau /viz + routes est du calibre déjà délégué à sonnet
  sur les tickets 0018-0021).
- `/newbie` pour toute commande à faire exécuter par l'utilisateur
  (réinjection du corpus, rebuild `memory`).
- `/handoff` en fin de session.

## Modifiés cette session (non commités)

- `docs/wayfinder/tickets/0029-correction-ciblee-des-extractions.md` —
  décisions du grilling + correction « six → huit types ».
- `docs/wayfinder/carte-graphe-memoire.md` — ligne « tranché au grilling,
  reste à livrer » pour le 0029.
- Ce handoff.

(De nombreux autres fichiers étaient déjà modifiés/non suivis avant la session
— transport-voix, voice-forge, tickets 0023-0035… — ils ne viennent pas d'ici.)
