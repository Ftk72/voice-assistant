---
label: wayfinder:grilling
statut: clos
assigne: claude (session 2026-07-18, grilling puis implémentation déléguée)
bloque-par: [0020-insight-du-llm-local]
carte: carte-graphe-memoire
---

# Trous structurels

## Question

La signature InfraNodus : les paires de communautés **peu connectées**,
présentées comme des questions à creuser. Son utilité pour une mémoire
personnelle d'assistant vocal est moins évidente que pour l'analyse de texte —
d'où un grilling d'abord, sur le graphe déjà parlant :

- quelle sémantique donner à un « trou » dans une mémoire personnelle
  (angle mort ? simple non-lien sans intérêt ?) ;
- comment le présenter sans bruit (suggestion dans l'insight LLM du ticket
  précédent ? lecture dédiée ?) ;
- ou décider, arguments en main, d'en faire moins que prévu.

Si le grilling conclut à une mise en scène, elle se livre dans ce ticket
(exécution incluse).

## Résolution

**Tranché au grilling puis livré le 2026-07-18** (délégué sonnet, vérifié par
l'agent principal : pytest 98 verts, ruff propre, relecture des fichiers
critiques).

- **Sémantique** : un trou est un **angle mort de la mémoire** — une question
  que l'assistant pourrait poser. Les lectures « fait descriptif banal » et
  « hygiène du graphe » sont écartées (la seconde relèverait d'un chantier
  d'ingestion, pas d'une mise en scène).
- **Mise en scène** : **insight + affordance discrète** — pas de mode visuel
  dédié (dessiner une absence est intrinsèquement confus). Des **puces
  structurées** sous le paragraphe d'insight (« Travail ↔ Maison (0 fait) —
  voir »), tirées du condensé typé, jamais parsées de la prose ; clic → la
  caméra cadre les deux communautés (barycentre + recul proportionnel au rayon
  englobant, `volerVersTrou`). Garde-fou hérité du 0019 : si une exploration
  ciblée a écrasé les communautés client, le clic recharge d'abord le graphe
  complet — jamais de cadrage faux.
- **Définition** (`detecter_trous()` dans `analyse.py`, TDD, 7 tests) : trou =
  paire de communautés reliées par **≤ 1 arête**, communautés de **≥ 3
  entités**, classement par **produit des tailles** décroissant (départage
  alphabétique), **top 3**. Constantes dans le code, aucun réglage UI : les
  puces suivent la narration, pas un slider.
- **Voix** : `CondenseGraphe.trous` nourrit le prompt du 0020 — section
  « Angles morts » + consigne de **terminer le paragraphe par au plus une
  question ouverte** sur un seul angle mort (uniquement s'il y en a).
  `raconter_memoire` hérite de tout via le condensé partagé — aucun nouvel
  outil MCP.
- Reste dû (HITL) : jugement de l'utilisateur à l'œil (`/viz` après rebuild de
  l'image `memory`) et à l'oreille (`raconter_memoire`).
