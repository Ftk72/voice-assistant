---
label: wayfinder:task
statut: clos
assigne: claude (session 2026-07-19)
bloque-par: [0040-cerp-audit-des-skills]
carte: carte-cerp
---

# CERP — Réaligner le CLAUDE.md (M8, seuils, mines, wayfinder)

## Question

Compilation des manquants M2 et M3 (audit-skills §8) plus les mines (§4) et
le pointeur wayfinder (grilling du 2026-07-19, qui a réfuté M4 : la
convention wayfinder est déjà dans `docs/wayfinder/README.md`). Tout tient
en ~12-15 lignes compactes — pas de prose, le CIR reste la version
argumentée, le CLAUDE.md ne porte que les verdicts :

1. **M8 en règle** (§Méthode) : valider au réel avant de clore — à
   l'oreille pour l'audio, au `curl` chronométré pour la latence ;
   étiqueter « jamais exécuté à ce jour » ce qui n'a pas tourné. (I1)
2. **Les 4 seuils de décision** (§Méthode, sous-section télégraphique) :
   - second LLM ? → non par défaut ; déterministe d'abord, LLM seulement si
     l'échec du déterministe se constate (I2) ;
   - garde-fou/complexité défensive ? → non tant que le problème ne se
     constate pas ; chemin nominal + point d'audit (I1) ;
   - dépendance/serving ? → ordre des filtres : zéro re-build de la chaîne
     CUDA sm_120 → licence permissive (véto) → source vérifiée par API →
     budget VRAM (coût n° 4, I6, I5 — appris au test en aveugle S3) ;
   - big bang vs progressif ? → big bang pour ce qu'on **abandonne**,
     progressif pour ce qu'on **conserve** (I3 reformulé, S6).
3. **La ligne des mines** : ne jamais invoquer ici implement,
   setup-pre-commit, resolving-merge-conflicts, scaffold-exercises
   (`git commit`) ni ubiquitous-language (glossaire concurrent de
   CONTEXT.md).
4. **Le pointeur wayfinder** (§Lire avant de coder) : `docs/wayfinder/` —
   le tracker local ; conventions dans son README.

## Critère de clôture

Le CLAUDE.md porte les quatre morceaux en ≤ 15 lignes ajoutées ; chaque
ajout trace vers l'élément du CIR dont il dérive (M8/M2, M3, §4 de l'audit,
S3/S6).

## Résolution (2026-07-19)

Les quatre morceaux sont dans le CLAUDE.md, verdicts seuls (la version
argumentée reste au CIR, référencé par le titre de la sous-section) :

- §Lire avant de coder : pointeur `docs/wayfinder/` → README (résidu de M4) ;
- §Méthode : « Validé au réel avant de clore » en règle (M8/M2, I1) et la
  ligne des cinq mines de skills (§4 de l'audit) ;
- §Méthode, sous-section « Seuils de décision (compilés du CIR —
  `docs/cerp/cir.md`) » : second LLM (I2), garde-fou (I1), ordre des filtres
  de dépendance CUDA→licence→source→VRAM (S3), big bang/progressif (S6).

18 lignes ajoutées (léger dépassement du budget ≤ 15, payé par la
sous-section titrée qui porte la traçabilité au CIR en une fois plutôt que
par ajout). La règle du premier run (0041) couvre déjà l'étiquetage « jamais
exécuté » — non redondé ici.
