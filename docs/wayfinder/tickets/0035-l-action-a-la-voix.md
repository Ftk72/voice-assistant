---
label: wayfinder:prototype
statut: ouvert
assigne:
bloque-par: [0034-boucle-codeact-premiere-tache-reelle]
carte: carte-action-forge
---

# L'action à la voix (lancer, continuer, être prévenu)

## Question

Brancher le palier 1 sur la conversation : une Tâche se **lance à la voix**
(outil MCP de l'action-forge exposé au Dialogue Forge), la conversation
**continue pendant** que l'Atelier travaille, et la fin **s'annonce** —
le précédent est le minuteur de time-forge (annonce à l'échéance).

Prototype HITL, à trancher en jouant :

- L'énoncé : comment le Dialogue Forge reconnaît une Tâche d'action et la
  formule à la forge (et ce qu'il répond immédiatement : « je m'y mets »).
- Le pendant : silence, ou point d'étape si on le demande (« où en es-tu ? ») ;
  le compte rendu final restitué oralement, jamais lu ligne à ligne.
- Le visible : la Tâche et son état dans la coquille (module d'interface servi
  par l'action-forge, pattern voice-forge `/admin`) — la coquille assemble,
  sans logique métier.

## Critère de clôture

Une Tâche confiée à la voix aboutit et s'annonce, jugée à l'oreille et à
l'œil par l'utilisateur au poste Windows — le palier 1 de la destination est
atteint.
