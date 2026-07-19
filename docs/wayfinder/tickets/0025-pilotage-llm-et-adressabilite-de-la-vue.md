---
label: wayfinder:grilling
statut: ouvert
assigne:
bloque-par: [0024-seance-de-validation-au-reel, 0028-transparence-facon-linkq]
carte: carte-graphe-memoire
---

# Pilotage du graphe par le LLM et adressabilité de la vue

## Question

Gradué de la brume le 2026-07-18 (grilling du même jour) : deux faces d'un même
mécanisme, à trancher **ensemble** — le canal pousserait une URL, la viz
écouterait `hashchange`.

1. **Adressabilité de la vue** : une URL qui capture l'état affiché (entité
   focalisée, profondeur, mode ponts…) — quelle grammaire, quels états valent
   d'être adressables, et `hashchange` comme mécanisme d'écoute côté `/viz`.
2. **Pilotage par le LLM pendant la conversation** : le canal de commande
   bidirectionnel du module dialogue A4 fait voler la caméra vers une entité
   pendant que l'assistant en parle à voix haute. Demande un canal inverse
   (MCP → coquille) : quelle architecture, sans logique métier côté coquille.

Le grilling tranche l'architecture et le périmètre (l'adressabilité seule a
peut-être déjà de la valeur) ; l'exécution suit dans ce ticket si tranché
(la carte porte l'exécution). Bloqué par la séance de validation : le pilotage
suppose la coquille validée au poste Windows (0022), et l'expérience vécue
dira si le vol de caméra pendant la parole a de la valeur. Bloqué aussi, depuis
le grilling du 2026-07-18, par la
[Transparence façon LinkQ](0028-transparence-facon-linkq.md) : le canal
question → requête → entités qu'elle établit est la brique que le pilotage
réutilise — le contrat se partage, il ne se duplique pas.

## Critère de clôture

Architecture et périmètre actés (ou renoncement argumenté), et le rendu livré
si la décision l'inclut.
