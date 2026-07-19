---
label: wayfinder:task
statut: clos
assigne: claude (session 2026-07-19)
bloque-par: [0040-cerp-audit-des-skills]
carte: carte-cerp
---

# CERP — Réconcilier la mémoire agent et les étiquettes de statut

## Question

Compilation du manquant M1 (audit-skills §8) : les étiquettes de statut
dérivent entre deux réconciliations (E1 : mémoire « zéro fork OpenWebUI »
morte depuis l'ADR 0009 ; E2 : docstrings « jamais exécuté » périmées sur
Graphiti ; quatrième instance : mémoire « conteneurisation » périmée sur
dialogue-forge). Décisions prises au grilling du 2026-07-19 — reste à
exécuter :

1. **Retouche immédiate des 3 fichiers mémoire périmés**
   (`workflow-voice-assistant.md` : retirer « zéro fork OpenWebUI » et le
   clone `/home/ftk/openwebui/` ; `MEMORY.md` : sa ligne d'index ;
   `preference-conteneurisation-maximale.md` : dialogue-forge n'est plus
   candidat, il tourne en Docker).
2. **Écrire les deux règles de réconciliation au CLAUDE.md §Méthode**
   (péremption par événement, jamais par âge — I8) :
   - *balayage déclenché par ADR* : chaque ADR accepté, la même session
     relit la mémoire agent et le §État particulier du CLAUDE.md et périme
     ce que l'ADR vient de tuer ;
   - *règle du premier run* : la session qui exécute un adaptateur réel
     pour la première fois retire l'étiquette « jamais exécuté à ce jour »
     (docstring + §État particulier) dans la même session.

Pas de mécanisme pour les dérives sans événement net (I1 : `/premisses` les
rattrape en entrée de tâche — ne rien bâtir tant qu'un trou ne se constate
pas).

## Critère de clôture

Les 3 fichiers mémoire sont vrais à la date d'exécution ; les deux règles
sont dans CLAUDE.md §Méthode ; chaque ajout trace vers M1/E1/E2/I8.

## Résolution (2026-07-19)

Prémisses vérifiées avant retouche : les trois péremptions confirmées sur
pièces, et `dialogue-forge` confirmé en Docker (service `dialogue` du
compose, build `./dialogue-forge`, port 8600) — la mémoire conteneurisation
avait donc bien une croyance morte. Retouches appliquées, chacune datée et
tracée au ticket dans le fichier même :

- `workflow-voice-assistant.md` : « zéro fork OpenWebUI » et le clone
  `/home/ftk/openwebui/` retirés (morts depuis l'ADR 0009), description
  alignée (E1) ;
- `MEMORY.md` : ligne d'index alignée ;
- `preference-conteneurisation-maximale.md` : dialogue-forge acté en Docker ;
  transport-voix reste natif Windows tant que l'impasse WebRTC tient (E4).

Les deux règles de réconciliation sont écrites au CLAUDE.md §Méthode en une
puce (balayage-par-ADR + règle du premier run, péremption par événement
jamais par âge — M1, E1/E2, I8). Aucun mécanisme pour les dérives sans
événement net : `/premisses` reste le filet (I1).
