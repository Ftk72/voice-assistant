---
label: wayfinder:prototype
statut: clos
assigne: session-2026-07-20
bloque-par: []
carte: carte-graphe-memoire
---

# Encodage visuel du type d'entité

## Question

Gradué de la brume le 2026-07-18 : les six types de l'ontologie (Personne,
Lieu, Organisation, Animal, Bien, Activité — `ontologie.py`) sont stockés en
label Neo4j mais jamais exposés par l'API (`NoeudGraphe`) ni rendus. Prototype
HITL (/prototype, l'utilisateur juge à l'œil dans `/viz`) :

- **Côté serveur (TDD)** : exposer le type dans `NoeudGraphe` — la petite
  tranche testable.
- **Côté rendu** : quel encodage pour quel type — forme du nœud, glyphe,
  trait ? — sans casser la palette Okabe-Ito des communautés (la couleur est
  prise) ni la lisibilité à l'échelle du graphe. Le corpus synthétique couvre
  les six types : jouable dès maintenant, au navigateur, sans la coquille.

**À-côté acté au grilling** : l'export d'une vue en image (bouton,
`canvas.toDataURL()`) se livre dans ce ticket — trivial, et c'est le véhicule
UI attendu.

## Critère de clôture

Un encodage validé à l'œil par l'utilisateur (ou renoncement argumenté),
livré dans `/viz` avec le type exposé par l'API sous test, et le bouton
d'export d'image présent.

## Résolution

Livré et **validé à l'œil le 2026-07-20** après deux tours d'itération HITL.

- **Prémisse corrigée en route** : le ticket datait du 2026-07-18 et parlait
  de « six types jamais exposés » — l'audit des prémisses a montré que
  l'exposition (`NoeudGraphe.type`) était déjà arrivée avec le ticket 0029
  (postérieur) et que l'ontologie compte en réalité **huit** types. Seul
  manquait un test contractuel verrouillant `type` dans le JSON de
  `/graph/complet` (ajouté).
- **Encodage retenu** : Personne reste la sphère nue du nœud (type le plus
  fréquent, pas de glyphe surajouté) ; les sept autres types portent une
  primitive 3D **pleine** (`MeshStandardMaterial`, pas de fil de fer) —
  cône (Lieu), boîte (Organisation), tétraèdre (Animal), dodécaèdre (Bien),
  icosaèdre (Aliment), capsule (Projet), tore (Activité) — calée au ras du
  rayon réel de la sphère, effacée en mode ponts (le losange prime). Deux
  ratés en route, corrigés au retour utilisateur : un premier jet en mesh
  plein trop gros/confus (retenté en fil de fer, jugé « moche »), puis
  repassé en formes pleines resserrées avec Personne en sphère — c'est cette
  troisième version qui est validée.
- **Filtre par type** : légende « Types » transformée en cases à cocher
  (même mécanique que les filtres provenance/obsolètes), état persistant
  entre rafraîchissements.
- **Export d'image** : bouton dans l'en-tête, `canvas.toDataURL("image/png")`,
  `rendererConfig.preserveDrawingBuffer` posé pour ne pas capturer un canvas
  vide.
- **Régression corrigée en route** : `encodageType.js` n'avait pas de route
  serveur dédiée (le pattern du dépôt sert chaque module `/viz/*.js` un par
  un, pas de mount statique générique) — l'import 404 cassait tout le script
  et effaçait la scène. Fix + test de non-régression
  (`test_le_module_encodage_type_est_servi`), même patron que
  `adressabilite.js`.
- Tests : `app/viz/encodageType.js` sous `node:test`
  (`tests/encodageType.test.mjs`, exécuté via l'image `node:22-slim` déjà
  présente en local — zéro téléchargement), suite pytest memory-forge
  complète et ruff verts tout du long.
