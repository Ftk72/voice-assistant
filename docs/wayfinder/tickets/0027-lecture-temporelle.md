---
label: wayfinder:prototype
statut: clos
assigne: claude (session 2026-07-20)
bloque-par: [0024-seance-de-validation-au-reel]
carte: carte-graphe-memoire
---

# Lecture temporelle

## Question

Gradué de la brume le 2026-07-18 (hérité des « lots B1 » de la carte
précédente ; la condition « une fois la surface belle » est remplie depuis la
Somptuosité 3D). Prototype HITL : un **curseur temporel** dans `/viz` sur
`valid_at`/`invalid_at` — les faits hors fenêtre s'estompent ou disparaissent,
la mémoire se regarde remonter le temps.

À explorer au prototype : la grammaire du curseur (borne unique « à cette
date » ou fenêtre ?), le sort des faits invalidés (estompés ou retirés ?),
et ce que ça coûte côté serveur (les dates sont-elles déjà dans ce que sert
l'API ?). Le corpus synthétique porte des faits invalidés pour le jouer.

Bloqué par la séance de validation : voir d'abord si la mémoire vécue donne
envie de remonter le temps — le verdict peut être un renoncement.

## Critère de clôture

Un curseur jugé à l'œil par l'utilisateur et livré (ou renoncement argumenté
consigné).

## Résolution

**Deuxième passe, après un grilling** (le premier jet estompait par
transparence : jugé « beaucoup trop subtil » au réel). L'absence se dit
désormais par la **teinte**, et l'alpha a disparu — un canal, un sens.
Décisions du grilling : **deux couleurs** (futur `#3a4150` ardoise, révolu
`#b5533c` rouille — un fait pas-encore-né et un fait périmé sont des objets
inverses) ; le **gris « obsolète » suit le curseur** (à une date passée, un
fait invalidé plus tard était vivant et reprend sa provenance) ; la **case
« obsolètes » reste sur « aujourd'hui »**, car la rendre temporelle ferait
retirer/réapparaître des liens pendant le glissement et **sauter le layout** ;
**liens seuls**, les nœuds ne bougent pas (ternir un nœud entrerait en
collision avec le mode focus, qui utilise déjà `COULEUR_ESTOMPEE_NOEUD`) ;
**pastilles nommées** dans le panneau plutôt qu'une opacité (sur du texte,
estomper nuit à la lecture sans rien apprendre — et c'est là qu'on apprend
les couleurs de la scène) ; **décomptes sous le curseur** (« 199 présents ·
344 à venir · 13 révolus »), qui tiennent lieu de légende et de point d'audit.

Couleurs **validées par calcul**, pas à l'œil (skill dataviz,
`validate_palette.js`, fond `#0e1013`) : séparation en vision normale et en
daltonisme au-dessus des seuils, la pire paire de la scène restant le
bleu↔vert **préexistant** du dépôt. Le faible contraste de `COULEUR_FUTUR`
est délibéré (ce qui n'existe pas encore doit reculer) et compensé, comme le
validateur l'exige, par le relief textuel — décomptes et pastilles.

Assumé : un **saut de couleur au premier pixel** de glissement (les faits
obsolètes passent du gris au rouille). Ce n'est pas un défaut mais une
frontière — à « maintenant » on lit l'état du monde, ailleurs on lit une
date — et le préserver garde intact l'invariant de non-régression.

Les trois questions du ticket tranchées avant de coder : **borne unique**
« à cette date » (pas de fenêtre — un fait est présent si `valid_at` est nul
ou ≤ T et `invalid_at` nul ou > T) ; **faits hors période estompés, jamais
retirés** (le layout 3D ne doit pas bouger quand le curseur se déplace) ;
**curseur au maximum par défaut**, la vue au chargement restant strictement
celle d'aujourd'hui — invariant de non-régression testé.

Coût serveur nul, contrairement à ce que le ticket redoutait : `valid_at` et
`invalid_at` étaient **déjà** sérialisés par l'API (`app/schemas.py`) et déjà
lus par `index.html` pour le filtre « obsolètes ». Seule route ajoutée : le
service du module ES lui-même.

Fichiers : `app/viz/lectureTemporelle.js` (module pur — `bornesTemporelles`,
`presentALaDate`, `etatTemporel`, `FACTEUR_OPACITE_HORS_PERIODE`),
`tests/lectureTemporelle.test.mjs` (11 tests `node:test`),
`app/routes/api.py` (route `/viz/lectureTemporelle.js`),
`tests/test_graph_viz.py` (test de cette route), `app/viz/index.html`
(curseur, étiquette de date, bouton « maintenant », estompage 3D et panneau).

Deux pièges rencontrés, consignés parce qu'ils se reproduiront :

- **L'estompage 3D passe par `linkColor`, jamais par `linkOpacity`.** Constaté
  au réel (« aucune différence quand je bouge le curseur ») : dans
  3d-force-graph, `linkOpacity` est une propriété **numérique globale**, pas un
  accesseur par lien — une fonction y devient `NaN` en silence. Le canal
  par-lien est `linkColor` renvoyant du `rgba()`, dont la lib extrait l'alpha
  pour le multiplier à `linkOpacity` (d'où `avecFacteurAlpha` dans le module,
  et `couleurDuLien` extrait dans `index.html`). Le piège a deux étages : le
  premier diagnostic (opacité absolue 0.5 au lieu d'un facteur, invisible sur
  une base de 0.55) était juste mais superficiel, et le corriger seul ne
  réparait rien. Aucun test ne pouvait attraper ça — d'où le test de
  non-régression qui verrouille désormais le contrat de la bibliothèque.
- **`node` n'existe pas en WSL** : les tests `.test.mjs` du dépôt ne tournent
  que par le binaire Windows, `"/mnt/c/Program Files/nodejs/node.exe" --test`.

**Validé à l'œil le 2026-07-20**, au troisième tour : estompage par alpha
d'abord invisible (véhicule `linkOpacity` inopérant), puis lisible mais jugé
trop subtil, puis retenu sous forme de teintes après grilling. Jugé sur la
mémoire réelle (556 faits datés, du 2024-07-01 au 2026-07-10, 87
invalidations jusqu'au 2027-03-18) — pas sur le corpus synthétique.
