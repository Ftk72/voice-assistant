---
label: wayfinder:prototype
statut: ouvert
assigne:
bloque-par: []
carte: carte.md
---

# L'assistant s'entend et se répond (l'annonce rentre par le micro)

## Question

Constaté au réel le 2026-07-20 (validation du ticket
[L'action à la voix](0035-l-action-a-la-voix.md)) : la conversation était
restée ouverte, micro vif, quand l'annonce de fin de Tâche est partie sur les
enceintes. **Le micro a capté l'annonce, le STT l'a transcrite, et l'assistant
a répondu à sa propre voix.** L'assistant se parle à lui-même.

Ce n'est pas un défaut de l'action-forge : c'est le premier cas où une
**annonce spontanée** tombe pendant une **conversation ouverte**. Le minuteur
de time-forge avait le même potentiel — il n'a simplement jamais été éprouvé
dans cette configuration.

**Hypothèse de cause, à vérifier avant de coder** (elle n'est pas établie) :
les deux sorties audio empruntent des chemins **disjoints** (CLAUDE.md
§ Plateforme). La parole de conversation sort par la coquille (natif Windows,
WebRTC) — dont la pile applique une annulation d'écho acoustique sur ce
qu'elle joue elle-même, ce qui explique que l'assistant ne se réponde pas
pendant un tour normal. L'annonce, elle, sort par le **Pont hôte**
(aplay/WSLg, ADR 0008) : elle ne transite jamais par WebRTC, donc l'AEC
**ignore son existence** et ne peut pas la soustraire du signal entrant. Le
mécanisme qui protège le cas nominal est structurellement aveugle au cas de
l'annonce.

Si l'hypothèse tient, aucun réglage de VAD ni de seuil ne la corrigera : c'est
une question d'architecture des canaux, pas de sensibilité.

À trancher en jouant :

- **Le canal** : l'annonce doit-elle passer par la coquille quand une
  conversation est ouverte (l'AEC la voit alors, et l'annonce devient un tour
  de parole) et par le Pont hôte seulement hors conversation ? C'est le
  correctif structurel — mais il fait dépendre time-forge et action-forge de
  l'état d'une conversation, qu'elles ignorent aujourd'hui.
- **La garde simple** : ou bien le transport ferme le micro pendant la durée
  de l'annonce (il faut alors que quelqu'un dise au transport qu'une annonce
  est en cours, et combien de temps). Moins juste, beaucoup moins cher.
- **La conséquence sur la mémoire** : le tour fantôme a-t-il été capté comme
  un vrai tour de parole utilisateur ? Si oui, l'assistant mémorise des faits
  qu'il a lui-même énoncés — à vérifier dans memory-forge, et à purger le cas
  échéant.
- **La généralité** : reproduire d'abord avec le **minuteur** de time-forge
  (annonce à l'échéance pendant une conversation ouverte). Si le minuteur
  déclenche la même boucle, le défaut est bien celui du canal d'annonce, pas
  celui de l'action-forge.

## Critère de clôture

Une annonce tombant en pleine conversation ouverte est entendue par
l'utilisateur **sans** que l'assistant se réponde à lui-même, jugé à l'oreille
au poste Windows — vérifié sur les deux sources d'annonce (minuteur time-forge
et fin de Tâche action-forge).
