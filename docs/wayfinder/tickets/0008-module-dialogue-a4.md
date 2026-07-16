---
label: wayfinder:task
statut: ouvert
assigne:
bloque-par: [0007-rtvi-reel-dans-la-pastille, 0004-voix-du-flux-appliquee-par-tour]
---

# Module dialogue (A4)

## Question

Livrer le module d'interface du dialogue, **servi par le Dialogue Forge**
(front A4 de la roadmap) — bloqué par « RTVI réel dans la pastille » (même
flux d'événements, enfin observé en réel) et « La voix du flux appliquée par
tour » (les sélecteurs voix/persona doivent produire l'effet promis) :

- Page web du forge, chargée en onglet console : encadré de conversation
  (chaque phrase affichée **au moment où sa synthèse est jouée** — RTVI,
  ADR 0010 décision 5 ; les phrases interrompues jamais affichées), menu
  **persona** (pilote — changer = nouvelle conversation), menu **voix**
  (déroge pour la conversation en cours, effet au tour suivant),
  historique du fil, indicateur d'outils appelés.
- Côté DF si manquant : endpoint de dérogation de voix (l'audit 2026-07-10 a
  confirmé `/interrompre` et la voix dans le flux ; la dérogation reste à
  vérifier via `/premisses` en ouverture de ticket).
- Critère de clôture : conversation vocale complète suivie depuis la console,
  transcriptions utilisateur affichées après leur tour (STT batch), phrases
  assistant au fil de la lecture.
