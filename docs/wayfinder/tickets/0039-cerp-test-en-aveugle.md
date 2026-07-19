---
label: wayfinder:grilling
statut: clos
assigne: claude (session 2026-07-19, HITL)
bloque-par: [0038-cerp-reconstruire-le-cir]
carte: carte-cerp
---

# CERP — Le test en aveugle (le CIR prédit, l'ingénieur répond)

## Question

Phase Predict, protocole acté au grilling du 2026-07-19 : sur **4 à 6
scénarios d'ingénierie inédits** (hors corpus — nouveaux composants,
dilemmes d'architecture, pannes plausibles), le CIR prédit **par écrit,
d'abord** : cadrage du problème, heuristiques activées, priorités,
compromis probables, architecture préférée, stratégie de validation,
approches rejetées. Puis l'utilisateur répond aux mêmes scénarios **sans
voir les prédictions** ; on compare, on score, on consigne les écarts.

HITL strict : l'agent ne répond jamais à la place du sujet. Produit
`docs/cerp/test-en-aveugle.md` (scénarios, prédictions, réponses,
comparaison) et la liste des révisions du CIR qu'exigent les écarts.
L'ampleur d'une éventuelle seconde boucle est au brouillard de la carte —
elle se juge au score.

## Critère de clôture

Le rapport de validation prédictive existe, le CIR est révisé (ou confirmé)
en conséquence — la compilation peut s'appuyer sur un modèle dont le pouvoir
prédictif est mesuré, pas supposé.
