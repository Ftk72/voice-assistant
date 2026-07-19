---
label: wayfinder:prototype
statut: ouvert
assigne:
bloque-par: [0024-seance-de-validation-au-reel]
carte: carte-graphe-memoire
---

# Lecture temporelle

## Question

Gradué de la brume le 2026-07-18 (hérité des « lots B1 » de la carte
précédente ; la condition « une fois la surface belle » est remplie depuis la
Somptuosité 3D). Prototype HITL : un **curseur temporel** dans `/viz` sur
`valid_at`/`invalid_at` — les faits hors fenêtre s'estompent ou disparaissent,
la mémoire se regarde remonter le temps.

À explorer au prototype : la grammaire du curseur (borne unique « à cette
date » ou fenêtre ?), le sort des faits invalidés (estompés ou retirés ?),
et ce que ça coûte côté serveur (les dates sont-elles déjà dans ce que sert
l'API ?). Le corpus synthétique porte des faits invalidés pour le jouer.

Bloqué par la séance de validation : voir d'abord si la mémoire vécue donne
envie de remonter le temps — le verdict peut être un renoncement.

## Critère de clôture

Un curseur jugé à l'œil par l'utilisateur et livré (ou renoncement argumenté
consigné).
