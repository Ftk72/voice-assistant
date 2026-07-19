---
label: wayfinder:map
cree: 2026-07-19
---

# Carte — Le jumeau d'ingénierie (CERP)

## Destination

Le **CIR** (Cognitive Intermediate Representation — le plus petit modèle
cognitif prédictif de l'ingénieur) est reconstruit depuis le corpus, **validé
en aveugle contre l'ingénieur lui-même**, puis **compilé** dans les artefacts
qui font agir : skills améliorés ou manquants, CLAUDE.md/mémoire agent
réalignés, arbres de décision. Fini quand les prochaines sessions d'agent
décident comme l'utilisateur — pouvoir prédictif mesuré à l'appui — et que
chaque artefact trace vers les éléments du CIR dont il dérive.

## Notes

- Protocole : CERP (Observe → Reconstruct → Validate → Compile → Predict).
  L'objectif n'est **pas** d'expliquer le dépôt : c'est de **prédire** les
  décisions futures de son auteur. Le CIR est l'artefact canonique — rien ne
  se compile qui n'en dérive ; aucun artefact non justifié par de l'évidence
  récurrente.
- Corpus d'évidence (acté au grilling du 2026-07-19) : le dépôt complet
  (code, docs, ADR, impasses, handoffs, cartes wayfinder, historique git) +
  `~/.claude/skills` + la mémoire agent du projet — en surveillant la
  **circularité** de ces deux derniers (déjà des condensés interprétés).
- Localisation : CIR et rapports dans `docs/cerp/` (versionnés, commités par
  l'utilisateur) ; les artefacts compilés vont là où ils agissent
  (`~/.claude/skills`, CLAUDE.md, mémoire agent).
- Discipline d'observation : observations séparées des interprétations ;
  les absences récurrentes comptent autant que les patterns ; chaque
  invariant du CIR porte évidence pour, évidence contre, alternatives,
  confiance, pouvoir prédictif — ce qui ne survit pas à la falsification
  est rejeté.
- Skills : `/premisses` en ouverture de chaque ticket ; `/delegate` pour les
  tickets AFK volumineux ; `/grilling` pour les HITL ; `/handoff` en fin de
  session.
- Constantes : tout en français ; jamais de `git commit` par l'agent.

## Décisions jusqu'ici

<!-- une ligne par ticket clos : gist + lien -->

- Le dépôt est observé : rapport factuel sourcé (patterns, absences, 13 ADR
  datés, hypothèses falsifiables isolées) dans `docs/cerp/observations-depot.md`
  — [0036](tickets/0036-cerp-observer-le-depot.md).
- La méthode déclarée est observée : impositions/interdits de 43 skills et de
  la mémoire agent, circularité tenue, 8 questions ouvertes déclaré-vs-pratiqué
  dans `docs/cerp/observations-methode.md` —
  [0037](tickets/0037-cerp-observer-la-methode.md).
- Le CIR existe et est falsifié sur pièces : 3 principes-mères, 8 invariants,
  fonction de coût, modèle de décision en 9 étapes, 4 rejets motivés, 7/8
  questions tranchées (Q7 → aveugle) dans `docs/cerp/cir.md` —
  [0038](tickets/0038-cerp-reconstruire-le-cir.md).
- Le CIR est validé en aveugle (prédictions scellées par SHA-256, 6 scénarios +
  2 questions, score 3,5/6 testables) et révisé en retouche ciblée : I4 confirmé
  et promu méta-invariant d'entrée (le sujet répond par le rite, le contenu est
  co-produit par la dyade), clause big bang de I3 reformulée (abandon → big
  bang / conservation → progressif), coût « re-build CUDA » inséré devant la
  licence, Q1 (granularité = maximiser l'AFK) et Q7 (skills rédigés par l'agent
  sur demande) closes — rapport `docs/cerp/test-en-aveugle.md` —
  [0039](tickets/0039-cerp-test-en-aveugle.md).
- Les 45 skills, le CLAUDE.md et la mémoire agent sont audités contre le CIR,
  verdict tracé ligne à ligne (12 conformes, 4 à améliorer, 29 injustifiés
  dont 5 mines, 5 manquants M1-M5, quatrième instance de la dérive des
  étiquettes trouvée) ; six chantiers de compilation candidats, aucun skill
  neuf justifié — rapport `docs/cerp/audit-skills.md` —
  [0040](tickets/0040-cerp-audit-des-skills.md).
- La compilation est graduée (grilling du 2026-07-19) : 2 tickets au lieu des
  six chantiers — [0041](tickets/0041-cerp-reconcilier-la-memoire-agent.md)
  (réconciliation mémoire + règles balayage-par-ADR et premier-run) et
  [0042](tickets/0042-cerp-realigner-le-claude-md.md) (M8, seuils, mines,
  pointeur wayfinder). Tranché sans ticket : M4 **réfuté** (la convention
  wayfinder vit déjà dans `docs/wayfinder/README.md` — croyance fausse de
  l'audit, corrigée) ; diagnosing-bugs adopté **tel quel** (CLAUDE.md porte
  déjà le branchement impasses) ; premisses retouché d'une ligne (exception
  E3) ; handoff **non** retouché (skill partagé, la convention du dépôt
  suffit). Règle générale : *les skills locaux se compilent, les skills
  partagés se surchargent par le CLAUDE.md.*
- La mémoire agent est réconciliée (3 fichiers retouchés, péremptions datées
  et tracées) et les deux règles de réconciliation — balayage-par-ADR et
  premier-run — sont au CLAUDE.md §Méthode (M1 compilé) —
  [0041](tickets/0041-cerp-reconcilier-la-memoire-agent.md).
- Le CLAUDE.md est réaligné : « validé au réel » en règle, les 4 seuils de
  décision (second LLM, garde-fou, filtres de dépendance CUDA→licence→
  source→VRAM, big bang/progressif), la ligne des 5 mines de skills et le
  pointeur wayfinder — M2, M3 et le résidu de M4 compilés ; la phase Compile
  est close, reste Predict (livrables 3 et 9 du brouillard) —
  [0042](tickets/0042-cerp-realigner-le-claude-md.md).

## Pas encore spécifié

- **Le modèle de décision d'ingénierie** (livrable 3) : forme exacte
  (document ? arbre ? les deux ?) — se précisera à la reconstruction du CIR.
- **Le rapport d'incertitudes final** (livrable 9) : ce qui reste non
  modélisable — s'écrira en clôture de carte, quand on saura ce qui a résisté.

## Hors périmètre

- **Expliquer le dépôt** (documentation, onboarding) : le CERP prédit
  l'auteur, il ne documente pas le produit — les README et cartes existants
  s'en chargent.
- **Modéliser d'autres sujets** que l'ingénieur du dépôt (l'agent lui-même,
  les modèles LLM) : un seul sujet, son auteur.
- **Généraliser hors de ce corpus** : le CIR vaut pour ce que l'évidence
  couvre ; l'étendre à d'autres dépôts de l'utilisateur serait une carte
  ultérieure, sur nouveau corpus.
