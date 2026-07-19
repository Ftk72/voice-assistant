---
label: wayfinder:task
statut: clos
assigne: claude (session 2026-07-19, délégué opus)
bloque-par: [0036-cerp-observer-le-depot, 0037-cerp-observer-la-methode]
carte: carte-cerp
---

# CERP — Reconstruire et falsifier le CIR

## Question

Phases Reconstruct + Validate (validation documentaire) : depuis les deux
rapports d'observation, reconstruire le **plus petit** modèle cognitif
prédictif — `docs/cerp/cir.md` : invariants d'ingénierie, heuristiques de
décision, priorités d'optimisation, instincts d'architecture, stratégies
d'abstraction et de décomposition, philosophies de validation / debug /
échec / compromis, seuils de décision, fonction de coût cognitive.

Discipline (notes de carte) : le POURQUOI, pas le QUOI ; chercher
l'explication **plus simple** avant d'ajouter une heuristique ; expliquer
les choix technologiques par des principes de plus haut niveau quand c'est
possible. Chaque invariant porte : évidence pour, évidence contre,
explications alternatives, confiance, pouvoir prédictif — **rejeter** ce qui
ne survit pas à la falsification. Distinguer conventions de projet /
contraintes externes / préférences personnelles. Confronter le déclaré
(méthode) au pratiqué (dépôt) : les écarts sont les trouvailles les plus
précieuses.

Inclut une première forme du **modèle de décision d'ingénierie**
(livrable 3) — sa forme définitive est au brouillard de la carte.

## Critère de clôture

`docs/cerp/cir.md` existe : minimal, falsifié sur pièces, chaque conclusion
traçable à une évidence observable — prêt pour le test en aveugle.

## Verdict (2026-07-19)

Livré : `docs/cerp/cir.md` — 3 principes-mères (réalité seule monnaie / un
seul cerveau, le reste bête et déterministe / contenir le rayon de souffle),
8 invariants I1–I8 aux cinq champs (pour/contre/alternatives/confiance/
pouvoir prédictif), fonction de coût (asymétrie clé : irréversibilité des
**données** ≫ du service), première forme du modèle de décision en 9 étapes
avec seuils, 6 écarts déclaré-vs-pratiqué (E1–E3 tensions vraies : « les
étiquettes de statut dérivent entre deux réconciliations » ; E4–E6 assumés),
4 rejets motivés (dont H-1 « réversibilité d'abord », tué par le big bang
de l'ADR 0009 choisi contre la recommandation de l'agent). 7 questions
ouvertes sur 8 tranchées ; Q7 (origine des skills sur mesure) indécidable
sur pièces → test en aveugle. Vérifié par l'agent principal : relecture
intégrale, périmètre au `git status`, pièces décisives contre-vérifiées
(ADR 0009 §Alternatives, mtimes mémoire, commits `7741a12`/`d02c03e`,
purge ADR 0011) — toutes exactes.
