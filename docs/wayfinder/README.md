# Tracker wayfinder local (markdown)

Le dépôt n'a pas de tracker d'issues accessible (`gh` absent) : la carte
wayfinder vit ici, en markdown versionné — souverain, comme le reste.

## Conventions (« Wayfinding operations »)

- **Une carte** : un fichier `carte*.md` à la racine, label `wayfinder:map` en
  frontmatter — plusieurs cartes (efforts) peuvent coexister. C'est un index :
  une décision vit dans son ticket, la carte la giste et la lie.
- **Un ticket** : un fichier `tickets/NNNN-slug.md` (numérotation unique,
  toutes cartes confondues). Son identité est son nom de fichier ; son titre
  (`# …`) est son nom lisible — on s'y réfère toujours par ce titre. Le
  frontmatter `carte:` dit à quelle carte il appartient (absent = `carte.md`,
  la carte historique).
- **Frontmatter d'un ticket** :
  - `label: wayfinder:research | prototype | grilling | task`
  - `statut: ouvert | clos`
  - `assigne:` — vide = non réclamé. Une session **réclame** un ticket en y
    mettant son nom **avant** tout travail.
  - `bloque-par: [NNNN-slug, …]` — blocage par convention de corps (pas de
    blocage natif en markdown). Un ticket est **débloqué** quand tous ses
    bloqueurs sont `statut: clos`.
- **La frontière** (tickets ouverts, débloqués, non réclamés) se calcule :
  `grep -l "statut: ouvert" tickets/*.md` puis filtrer sur `bloque-par` clos
  et `assigne` vide.
- **Résolution** : la réponse s'écrit dans le ticket sous `## Résolution`,
  le `statut` passe à `clos`, et une ligne pointeur s'ajoute aux
  « Décisions jusqu'ici » de la carte.
- **Jamais plus d'un ticket résolu par session.**
