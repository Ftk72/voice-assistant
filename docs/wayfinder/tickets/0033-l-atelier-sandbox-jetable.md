---
label: wayfinder:task
statut: ouvert
assigne:
bloque-par: [0031-contrat-de-l-action-forge]
carte: carte-action-forge
---

# L'Atelier : la sandbox Docker jetable

## Question

Livrer le bac à sable du palier 1, sur le contrat acté en
[Contrat de l'action-forge](0031-contrat-de-l-action-forge.md) :

- **Image de l'Atelier** : outillée (bash, Python 3.12, uv, ffmpeg, outils
  fichiers), construite dans compose, sans réseau par défaut (la politique
  réseau est en brouillard de carte).
- **Cycle de vie** : la forge (conteneurisée) pilote des conteneurs jetables
  frères via le socket Docker — un Atelier par Tâche, limites CPU/RAM/temps,
  détruit après compte rendu ; répertoire d'échange monté selon le contrat.
- **TDD ports/adaptateurs** : port ABC `Atelier` (exécuter une Action, lire
  un résultat), **adaptateur factice** par défaut (zéro Docker, utilisé par
  les tests), adaptateur réel Docker documenté « jamais exécuté à ce jour »
  jusqu'à son premier run.

Piège connu à ne pas répéter : monter le socket Docker donne à la forge un
pouvoir root de fait sur l'hôte — le contrat (0031) doit dire qui a le droit
de parler à la forge, et l'Atelier lui-même ne voit jamais le socket.

## Critère de clôture

`uv run pytest` et `ruff` verts sur la forge avec l'Atelier factice ;
l'adaptateur réel lance, borne et détruit un conteneur au réel (smoke test) ;
l'image de l'Atelier se construit dans compose.
