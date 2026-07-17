---
label: wayfinder:prototype
statut: ouvert
assigne:
bloque-par: [0013-liste-complete-des-voix-enrolees]
---

# Réglage grand public voix + persona dans la coquille

## Question

Choix utilisateur au re-wayfinding 2026-07-17 : **surface neuve, grand public**
(la console A4 reste l'outil technique de suivi ; on veut EN PLUS un vrai
réglage propre). L'utilisateur choisit **son persona** et **sa voix** parmi la
**liste complète des voix enrôlées**, hors du contexte debug de la console.

Contraintes :
- **ADR 0009** : la coquille n'héberge **aucune logique métier** — le réglage
  est une **page servie par une forge**, montée dans la coquille (pattern
  voice-forge `/admin`, DF `module_dialogue` en iframe).
- S'appuie sur le contrat cross-forge tranché en **0013** pour la liste
  complète des voix.
- Rapport persona↔voix déjà modélisé (un persona porte une voix par défaut ;
  choisir une voix = dérogation) — cf. `personas/`, endpoint de dérogation DF
  livré en 0008.

Étape 1 = **prototype** (skill `/prototype`) de l'UX pour réagir concrètement
(où vit le réglage dans la coquille, comment persona et voix s'articulent,
aperçu ?), avant de livrer.

## Périmètre

- Concevoir (prototype) puis **livrer** le réglage : page servie par une forge,
  montée dans la coquille, sélection persona + voix (liste complète), effet réel
  sur la conversation.
- **Hors périmètre** : la console A4 (inchangée) ; l'enrôlement/clonage
  (0005/0012).

## Critère de clôture

Depuis la coquille, un utilisateur choisit persona et voix parmi toutes les voix
enrôlées, proprement (hors console de debug), et l'assistant en tient compte —
validé au poste Windows.
