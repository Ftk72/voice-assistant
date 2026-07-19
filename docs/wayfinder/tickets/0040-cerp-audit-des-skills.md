---
label: wayfinder:task
statut: clos
assigne: claude (session 2026-07-19, AFK)
bloque-par: [0039-cerp-test-en-aveugle]
carte: carte-cerp
---

# CERP — Audit des skills contre le CIR validé

## Question

Première marche de la phase Compile : confronter chaque skill de
`~/.claude/skills` (et les automatismes de CLAUDE.md / mémoire agent) au CIR
validé — pour chacun : quel(s) élément(s) du CIR il sert, où il le
contredit, ce qu'il rate (heuristiques du CIR qu'aucun skill ne porte), ce
qu'il surspécifie (rituels sans évidence récurrente).

Produit `docs/cerp/audit-skills.md` : le verdict par skill
(conforme / à améliorer / manquant / injustifié), chaque verdict référençant
les éléments du CIR dont il dérive. **Ne compile rien encore** : c'est
l'audit qui fera graduer le brouillard « compilation » de la carte en
tickets concrets (quels skills, quels arbres, quel réalignement CLAUDE.md).

AFK, délégable.

## Critère de clôture

L'audit existe, traçable au CIR ligne à ligne — les tickets de compilation
peuvent se spécifier dessus sans re-discuter.

## Résolution (2026-07-19)

`docs/cerp/audit-skills.md` : 45 skills audités, chaque verdict tracé aux
éléments du CIR (I-x, E-x, coût n° n, M-n, Q-n, S-n). Bilan : 12 conformes
(la couche sur mesure + les adoptés sont déjà la compilation de fait du CIR,
Q7), 4 à améliorer (premisses/E3, handoff/E5, wayfinder/convention non
documentée, diagnosing-bugs/registre d'impasses absent), 29 injustifiés
(couche dormante E6 + autres contextes), dont 5 mines actives s'ils étaient
invoqués (4 skills qui commitent, ubiquitous-language qui dédouble le
glossaire de I7). Hors skills : CLAUDE.md et 3 fichiers de mémoire agent sur 6
à améliorer — l'audit a trouvé une **quatrième instance** du constat
transversal §7 du CIR (mémoire « conteneurisation » périmée sur
dialogue-forge, déjà en Docker). Cinq manquants (M1-M5), le plus rentable
étant M1 : aucun rite ne réconcilie les étiquettes de statut (mémoire ↔ ADR,
docstrings « jamais exécuté » ↔ runs réels). Six chantiers de compilation
candidats listés en §9 — aucun skill neuf justifié : le CIR se compile en
retouches et réalignement, pas en artefacts nouveaux.
