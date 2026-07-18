---
label: wayfinder:prototype
statut: clos
assigne: claude (session 2026-07-18)
bloque-par: [0016-corpus-synthetique-de-memoire]
carte: carte-graphe-memoire
---

# Somptuosité 3D et balade fluide

## Question

Le cœur de l'effort : porter `/viz` au niveau esthétique et navigationnel
d'InfraNodus, en 3D principale. À prototyper et juger à l'œil sur le corpus
synthétique :

- **étiquettes** lisibles en 3D (sprites/texte) qui apparaissent selon le zoom
  et la centralité, sans bouillie visuelle ;
- **focus** : au survol/clic, le voisinage s'illumine et le reste s'estompe ;
- **caméra** qui glisse vers le nœud cliqué (transitions animées, jamais de
  saut sec) ;
- **matière** : couleurs de communautés retravaillées, éventuels bloom/halo,
  arêtes courbes ou particules — ce que three.js permet sans ruiner la fluidité ;
- la **bascule 2D** conservée et non cassée.

HITL : plusieurs allers-retours de rendu attendus ; l'utilisateur tranche à
l'œil ce qui est somptueux et ce qui est gadget.

## Résolution

**Livré et validé au réel le 2026-07-18**, avec deux allers-retours de bug
(un chaînage `.addPass().addPass()` invalide qui bloquait tout le script, et
`three.core.min.js` manquant — les builds récentes de three.js scindent le
module en deux fichiers) avant que le rendu s'affiche.

- **Vendoring complet** (décision de l'utilisateur « vendore tout ce que tu
  peux ») : `three.js` 0.179.0 (core + module), `three-spritetext`, le
  pipeline de post-traitement complet (`EffectComposer`, `RenderPass`,
  `ShaderPass`, `MaskPass`, `OutputPass`, `UnrealBloomPass`, `OutlinePass`) —
  ~1,8 Mo, zéro dépendance CDN (ADR 0010 pt.6). La route `/viz/vendor/{...}`
  est passée en `:path` pour servir l'arborescence imbriquée des modules ES.
  L'architecture bascule en `<script type="module">` + import map (`"three"`
  → le fichier vendoré) — `3d-force-graph.min.js` reste un script classique
  (UMD, `window.ForceGraph3D`), les deux cohabitent.
- **Étiquettes** : vraies sprites 3D (`three-spritetext`, mémoïsées par nœud,
  jamais recréées — seules leurs propriétés mutent), zoom sémantique (nœuds
  dominants, proches de la caméra, ou dans le focus courant ; plafond 60).
- **Focus** : survol/clic estompe le reste (couleur + largeur de lien +
  particules) et ajoute un **halo `OutlinePass`** sur le nœud en focus — plus
  franc que la simple dimmed-color initialement prévue, rendu possible par le
  vendoring three.js complet.
- **Caméra** : vol animé (`cameraPosition`, 900 ms) vers tout nœud cliqué.
- **Matière** : bloom léger (`UnrealBloomPass` sur le composer interne de
  3d-force-graph, exposé via `postProcessingComposer()`), arêtes courbes,
  particules directionnelles sur les liens non obsolètes, vignette CSS.
- **Palette accessible** (issue du `/grill-me` post-livraison, décision
  explicite de l'utilisateur — « l'accessibilité est un droit pour tous ») :
  la palette d'origine (angle doré HSL) remplacée par Okabe-Ito (8 teintes
  colorblind-safe, cyclées avec éclaircissement au-delà de 8 communautés) ;
  accent recentré en magenta (`#ff3ea5`) pour ne plus collisionner avec
  l'orange de la palette catégorielle.
- **Vue d'entrée allégée** (issue du même grilling) : le chargement initial
  ne montre plus les 264 entités d'un coup mais les nœuds dominants
  (centralité ≥ 0,4) + leur voisinage direct ; le bouton « Graphe complet »
  et toute exploration ciblée restent des échappatoires vers la vue exhaustive
  (`state.vueAllegee`, `chargerGrapheComplet({ allege })`).
- **Six pistes graduées en fog** sur la carte (pilotage caméra par le LLM,
  vue hiérarchique par communautés, minimap, adressabilité URL, encodage
  visuel du type d'entité, export image) ; une écartée (retour sonore —
  spéculation sans ancrage dans la recherche ni demande de l'utilisateur).
