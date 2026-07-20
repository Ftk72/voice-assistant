---
label: wayfinder:task
statut: clos
assigne:
bloque-par: []
carte: carte-graphe-memoire
---

# Séance de validation au réel (jugements dus 0018-0022)

## Question

Gradué de la brume le 2026-07-18 : quatre tickets clos de la carte attendent
encore le jugement de l'utilisateur — c'est la **porte** derrière laquelle
patiente la moitié du brouillard restant (vue hiérarchique, minimap, parité 2D,
performance dense). Task HITL : rien à décider ici, mais rien ne se tranche
sans l'expérience vécue.

La séance, au poste Windows (coquille) et au navigateur (`/viz`) :

1. **Sujets dominants nommés** (0018) — jugement à l'œil : légende latérale,
   noms déterministes, vol de caméra au clic.
2. **Insight en français du LLM local** (0020) — jugement à l'œil (panneau
   « Insight ») et à l'oreille (`raconter_memoire`). **Préalable : rebuild de
   l'image `memory`** (le conteneur diverge, cf. impasse du 2026-07-18 —
   rebuild par l'utilisateur, bonne connexion).
3. **Trous structurels** (0021) — puces d'angles morts sous le récit, clic →
   caméra sur les deux communautés ; la question ouverte en fin d'insight.
4. **Le graphe dans la coquille** (0022) — onglet « Graphe » dans la console
   Tauri au poste Windows : chargement paresseux, CSP, scène WebGL fluide.

Chaque commande à exécuter par l'utilisateur suit `/newbie`. Les observations
se notent au fil de l'eau : ce qui déçoit nourrit la graduation du brouillard.

## Critère de clôture

Les quatre livraisons sont jugées (validées ou recalées avec observations
notées dans la résolution), et le brouillard « à l'usage » de la carte peut
être re-trié à la lumière de l'expérience vécue.

## Résolution

**Séance tenue et validée par l'utilisateur le 2026-07-20.** Préalable levé :
image `memory` rebuildée (`docker compose up -d --build memory`, `/health` ok)
pour résorber la divergence du conteneur signalée le 2026-07-18. Les quatre
livraisons (sujets dominants 0018, insight français du LLM local 0020, trous
structurels 0021, graphe dans la coquille 0022) sont **jugées bonnes au réel**
(œil `/viz`, oreille `raconter_memoire`, onglet « Graphe » de la coquille) —
aucun recalage. La porte est franchie : le brouillard « à l'usage » de la carte
peut être re-trié à la lumière de l'expérience vécue.
