---
label: wayfinder:map
cree: 2026-07-18
---

# Carte — Le graphe mémoire somptueux

## Destination

Le graphe mémoire, peuplé d'un **corpus synthétique** couvrant les cas limites,
s'explore **depuis la coquille** avec l'aisance et la beauté d'InfraNodus —
**3D principale, 2D en bascule**, navigation fluide (caméra qui glisse, focus
qui estompe, étiquettes lisibles selon le zoom) — et il **raconte** sa
mémoire : sujets nommés, ponts entre communautés, insight en français du LLM
local, trous structurels. Chaque tranche est validée à l'œil de l'utilisateur,
au réel.

Cadrage acté au grilling du 2026-07-18 : **exécution incluse** (override
wayfinder « plan, don't do », comme la carte précédente) ; moteur conservé
(3d-force-graph vendoré, `numDimensions` pour la bascule 2D) ; tout le métier
reste dans memory-forge (`/viz`), la coquille ne fait qu'assembler.

## Notes

- **Exécution incluse** : les tickets livrent le rendu, pas seulement la
  décision. Type dominant : `prototype` (HITL — l'utilisateur juge à l'œil).
- Ordre acté des chantiers : corpus → beauté/navigation 3D → sujets → ponts →
  insight LLM → trous structurels → coquille. L'insight (4) passe **avant**
  les gaps (3) : valeur immédiate, les gaps pourront le nourrir ensuite.
- Skills : `/impasses` avant tout diagnostic ; `/premisses` en ouverture de
  chaque ticket ; `/prototype` pour les tickets prototype ; `/handoff` en fin
  de session.
- Constantes : tout en français ; jamais de `git commit` par l'agent ;
  zéro CDN — toute bibliothèque se vendorise ; jamais de logique métier côté
  coquille ; TDD pour tout ce qui est testable côté serveur (analyse.py).
- Stack en place : communautés (Louvain) et centralité déjà calculées côté
  serveur ([analyse.py](../../memory-forge/app/viz/analyse.py)) ; UI actuelle
  dans [index.html](../../memory-forge/app/viz/index.html) ; LLM local
  llama.cpp port 8001, memory-forge port 8200, Neo4j 7474/7687.

## Décisions jusqu'ici

<!-- une ligne par ticket clos : gist + lien -->

- [Corpus synthétique de mémoire](tickets/0016-corpus-synthetique-de-memoire.md)
  — **livré au réel le 2026-07-18** : 264 entités / 555 faits injectés en
  Cypher direct (l'ingestion LLM ne garantit pas la topologie), rejouable et
  purgeable (`corpus: "synthetique"`), tous les cas limites sous contrat de
  test ; image `memory` rebuildée (routes viz désormais servies). Débloque
  « Somptuosité 3D et balade fluide ».
- [Somptuosité 3D et balade fluide](tickets/0017-somptuosite-3d-et-balade-fluide.md)
  — **livré et validé au réel le 2026-07-18** : étiquettes sprite 3D
  (`three-spritetext`), halo `OutlinePass` + bloom léger sur le focus, vol de
  caméra animé, palette Okabe-Ito colorblind-safe, vue d'entrée allégée
  (dominantes + voisinage plutôt que 264 entités d'un coup). A exigé de
  vendorer `three.js` complet (core + post-traitement, ~1,8 Mo, zéro CDN) et
  de basculer `/viz` en modules ES + import map. Un `/grill-me` post-livraison
  a gradué six pistes en fog (voir ci-dessous) et écarté le retour sonore.
- [Sujets dominants nommés](tickets/0018-sujets-dominants-nommes.md) —
  **tranché et livré le 2026-07-18** (délégué sonnet) : nommage déterministe
  (top-3 entités les plus centrales par communauté, pas de LLM — réservé à
  0020), légende latérale cliquable qui fait voler la caméra vers l'entité
  centrale de la communauté. Jugement visuel encore dû par l'utilisateur.
- [Ponts entre communautés](tickets/0019-ponts-entre-communautes.md) —
  **tranché et livré le 2026-07-18** : prototype à 3 variantes dans `/viz`,
  verdict utilisateur variante C « Squelette des ponts » — un *mode* (case
  « ponts » + seuil 2-10 dans l'en-tête) : ponts en losanges blancs, arêtes
  inter-communautés ambrées, tout le reste terni. Pas de liste latérale, pas
  d'intermédiarité (le Brandes du prototype n'a pas survécu au verdict —
  `analyse.py` inchangé). Prémisse fausse relevée : l'intermédiarité n'était
  pas « déjà calculée ».
- [Insight en français du LLM local](tickets/0020-insight-du-llm-local.md) —
  **tranché et livré le 2026-07-18** : appel direct llama.cpp (port ABC
  `GenerateurInsight`, factice + réel OpenAI-compat), condensé serveur
  (sujets/ponts/stats, jamais le graphe brut), panneau « Insight » à bouton
  dans `/viz`, outil MCP `raconter_memoire` orienté voix. Adaptateur réel
  smoke-testé : 93 s au premier appel, 9,1 s en régime. Jugement visuel
  encore dû par l'utilisateur (rebuild `memory` requis).
- [Trous structurels](tickets/0021-trous-structurels.md) — **tranché au
  grilling et livré le 2026-07-18** (délégué sonnet) : un trou = angle mort de
  la mémoire (question que l'assistant pourrait poser), pas de mode visuel —
  insight + puces cliquables sous le récit (clic → caméra sur les deux
  communautés). `detecter_trous()` en TDD (≤ 1 arête, communautés ≥ 3 entités,
  top 3 par produit des tailles), le prompt du 0020 finit par au plus une
  question ouverte sur un angle mort. Jugement œil/oreille encore dû.
- [Le graphe dans la coquille](tickets/0022-le-graphe-dans-la-coquille.md) —
  **livré le 2026-07-18** (délégué haiku) : onglet « Graphe » dans la console
  Tauri, iframe vers `/viz` (pattern A4) en chargement paresseux (`data-src`
  promu à la première visite — la scène WebGL ne se paie pas au démarrage),
  CSP `frame-src` étendue à 8200. Le verrou était la CSP Tauri, pas CORS.
  Validation au réel au poste Windows encore due.

## Pas encore spécifié

- **Pilotage du graphe par le LLM pendant la conversation** (grilling
  2026-07-18) : le canal de commande bidirectionnel du module dialogue A4
  pourrait faire voler la caméra vers une entité pendant que l'assistant en
  parle à voix haute. « Insight en français du LLM local » (clos) a fixé ce
  que le LLM interroge aujourd'hui : le condensé (sujets/ponts/stats) via
  `raconter_memoire` — le pilotage caméra demanderait un canal inverse
  (MCP → coquille), à trancher avec l'adressabilité de la vue ci-dessous.
- **Adressabilité de la vue** (URL qui capture entité/profondeur affichées,
  même grilling) : probablement le même mécanisme technique que le pilotage
  LLM (le canal pousserait une URL, la viz écoute `hashchange`) — à trancher
  ensemble plutôt que deux fois.
- **Vue hiérarchique par communautés** (méga-nœuds cliquables avant les
  entités individuelles) : plus ambitieuse que la vue allégée livrée en 0017 ;
  à réévaluer une fois vécue l'expérience actuelle sur un vrai usage.
- **Minimap** : utile si la navigation en profondeur devient courante ; le
  bouton « Graphe complet » sert déjà d'échappatoire « je suis perdu ».
- **Encodage visuel du type d'entité** (Personne, Lieu, Organisation, Animal,
  Bien, Activité — `ontologie.py`) : stocké en label Neo4j, jamais exposé par
  l'API (`NoeudGraphe`) ni rendu. Mériterait un prototype dédié (quelle forme
  pour quel type, lisibilité à l'échelle du graphe).
- **Export d'une vue en image** (comme InfraNodus) : techniquement trivial
  (`canvas.toDataURL()`), probablement un à-côté d'un futur ticket UI plutôt
  qu'un ticket à part.
- **Performance sur graphe dense** : si le corpus synthétique fait ramer le
  rendu (étiquettes sprites, effets), un chantier LOD/optimisation se
  ticketera. Option de repli notée en recherche : Cosmograph/cosmos.gl
  (GPU-natif layout + rendu, tient le million de nœuds) si le corpus grossit
  un jour bien au-delà de ce que 3d-force-graph (physique CPU) encaisse — pas
  un changement à faire maintenant.
- **Parité de la bascule 2D** : quels effets 3D (focus, étiquettes, caméra)
  doivent survivre en 2D, à trancher à l'usage.
- **Lecture temporelle** (curseur sur `valid_at`/`invalid_at`, hérité des
  « lots B1 » de la carte précédente) : à arbitrer une fois la surface belle —
  peut devenir un ticket ou rester hors périmètre.
- **Revalidation sur mémoire réelle** : une fois la vraie mémoire densifiée
  par l'usage, vérifier que beauté et analyses tiennent hors synthétique.

## Hors périmètre

- **Analyse de texte libre façon InfraNodus** (coller un texte arbitraire pour
  le cartographier) : memory-forge visualise sa mémoire, il ne devient pas un
  outil d'analyse documentaire.
- **Édition du graphe** au-delà de l'oubli d'entité existant (fusion de nœuds,
  renommage, création manuelle de faits).
- **Retour sonore sur les interactions du graphe** (grilling 2026-07-18,
  écarté par l'utilisateur) : le canal audio du projet est dédié à la voix de
  l'assistant (ADR 0007, host-bridge) ; des effets UI y créeraient de la
  confusion plutôt que de la valeur.
- **C1 proactivité, C3 identification du locuteur, C4 vision d'écran** — la
  roadmap « Ensuite » reste hors carte.
