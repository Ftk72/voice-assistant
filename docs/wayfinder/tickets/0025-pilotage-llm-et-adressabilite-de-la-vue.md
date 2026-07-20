---
label: wayfinder:grilling
statut: clos
assigne:
bloque-par: [0024-seance-de-validation-au-reel, 0028-transparence-facon-linkq]
carte: carte-graphe-memoire
---

# Pilotage du graphe par le LLM et adressabilité de la vue

## Question

Gradué de la brume le 2026-07-18 (grilling du même jour) : deux faces d'un même
mécanisme, à trancher **ensemble** — le canal pousserait une URL, la viz
écouterait `hashchange`.

1. **Adressabilité de la vue** : une URL qui capture l'état affiché (entité
   focalisée, profondeur, mode ponts…) — quelle grammaire, quels états valent
   d'être adressables, et `hashchange` comme mécanisme d'écoute côté `/viz`.
2. **Pilotage par le LLM pendant la conversation** : le canal de commande
   bidirectionnel du module dialogue A4 fait voler la caméra vers une entité
   pendant que l'assistant en parle à voix haute. Demande un canal inverse
   (MCP → coquille) : quelle architecture, sans logique métier côté coquille.

Le grilling tranche l'architecture et le périmètre (l'adressabilité seule a
peut-être déjà de la valeur) ; l'exécution suit dans ce ticket si tranché
(la carte porte l'exécution). Bloqué par la séance de validation : le pilotage
suppose la coquille validée au poste Windows (0022), et l'expérience vécue
dira si le vol de caméra pendant la parole a de la valeur. Bloqué aussi, depuis
le grilling du 2026-07-18, par la
[Transparence façon LinkQ](0028-transparence-facon-linkq.md) : le canal
question → requête → entités qu'elle établit est la brique que le pilotage
réutilise — le contrat se partage, il ne se duplique pas.

## Décisions (grilling du 2026-07-20)

Les deux bloqueurs (0024, 0028) sont clos : le grilling tranche. Les deux faces
s'unifient autour d'**un seul point d'entrée `hashchange`** — l'adressabilité le
définit, le pilotage le réutilise.

### Périmètre : adressabilité livrée ici, pilotage tranché mais différé

- **On livre l'adressabilité seule** dans ce ticket ; le pilotage a son
  architecture actée ci-dessous mais son exécution est différée (canal inverse
  non payé tant que l'usage ne le réclame pas).

### Adressabilité de la vue (à livrer, la carte porte l'exécution)

- **Grammaire d'URL (hash)** :
  `#focus=<nom>&surligner=<nom,nom>&prof=<n>&ponts=<seuil>&2d=1`. `focus` +
  `surligner` = le contrat `EtatVue` de 0028 (partagé, pas dupliqué) ; `prof`,
  `ponts` (présent = mode on, valeur = seuil), `2d` = les molettes durables.
  **Exclus** : panier « et si ? » (0030, éphémère) et `survol` (transitoire).
- **Miroir parallèle** (pas d'entonnoir unique) : la manipulation directe
  validée (0017-0022) est **conservée** ; chaque action reflète son état dans
  le hash ; un écouteur `hashchange` rejoue l'état sur navigation *externe*
  (URL collée, bouton précédent, hash poussé par le pilotage). Garde anti-boucle
  (une écriture-miroir ne re-déclenche pas l'écouteur). *Big bang pour ce qu'on
  abandonne, progressif pour ce qu'on conserve.*
- **Réflexion par `replaceState`** : URL-miroir toujours copiable, sans empiler
  d'historique navigable (évite le spam du curseur `seuil-ponts` et de la
  recherche au fil de la frappe). L'undo de vue s'ajoutera si l'usage le réclame.
- **`focus` en explore-to-fetch** : un `focus` sur une entité absente de la vue
  allégée déclenche `explorer(focus)` à la profondeur `prof` (le fetch ciblé
  déjà validé) — une URL partagée n'est jamais muette. **`focus` prime sur
  `ponts`** (`explorer()` écrase les communautés et suspend le mode ponts) : le
  mode ponts ne s'applique que sans `focus`. Entité inconnue → statut, pas de
  plantage.

### Pilotage du graphe par le LLM (architecture actée, exécution différée)

- **Déclencheur : outil MCP dédié `piloter_graphe(entites: list[str])`** (et non
  un piggyback sur `interroger_memoire`) — le pilotage vole aussi en
  conversation libre, et l'intention devient un signal explicite et détectable.
  Plusieurs entités : `surligner` = toutes les résolues, `focus` = la première ;
  non résolues nommées franchement dans l'accusé oral, sans bloquer les autres.
  Description MCP orientée voix : « montre l'entité pendant que tu en parles,
  n'annonce pas la manip ».
- **Calcul de l'outil** : résolution floue **réutilisée de 0028**
  (casse/accents/sous-chaîne) ; publie `EtatVue{focus, surligner}` ; pas de
  voisinage calculé serveur (le `focus` déclenche l'explore-to-fetch côté /viz).
  Accusé oral franc si rien ne résout (« Je ne trouve pas X »).
- **Canal : SSE même-origine** depuis memory-forge (`GET /viz/evenements`) ;
  `/viz` (servie par memory-forge, même origine) l'écoute en `EventSource`.
  **Zéro logique côté coquille** — elle héberge l'iframe, rien d'autre ; marche
  aussi en navigateur direct sur `/viz`. Broadcaster asyncio en process (service
  mono-process, `uvicorn.run` sans `workers` — viable). *(Écarté : le routage
  via le transport voix + console, qui traversait trois composants et mettait de
  la logique dans la coquille.)*
- **Application via le hash** : l'événement SSE fait `location.hash =
  sérialiser(EtatVue)` → l'écouteur `hashchange` de l'adressabilité l'applique.
  Un seul point d'entrée pour les deux faces ; toute vue pilotée devient
  aussitôt une URL partageable. *(Écarté : `appliquerVue` direct, qui aurait
  fait diverger les deux chemins.)*
- **SSE avec mémoire du dernier état** : memory-forge garde le dernier `EtatVue`
  publié et l'envoie à toute nouvelle connexion `EventSource` → l'onglet Graphe
  ouvert tardivement reflète la dernière chose montrée. **Pas d'auto-bascule
  d'onglet** (ce serait de la logique dans la coquille).

### Contrat partagé (le fil rouge)

Les deux faces convergent : `EtatVue{surligner, focus}` (0028) ⇄ hash ⇄
`hashchange` ⇄ mécanique de focus/`appliquerVue` existante. L'adressabilité
définit la sérialisation hash ; le pilotage n'a qu'à écrire ce hash via SSE.

## Critère de clôture

Architecture et périmètre actés (fait au grilling du 2026-07-20), et le rendu
**adressabilité** livré (TDD + validation au réel, session ultérieure — le cap
d'un ticket résolu par session est atteint pour la session du grilling). Le
pilotage reste tranché et différé : son exécution se replanifiera à l'usage.

## Résolution

**Adressabilité livrée en TDD et validée au réel le 2026-07-20** (implémentation
déléguée à sonnet, vérifiée par l'agent principal). Le pilotage LLM (SSE) reste
**tranché et différé** — rien de SSE/`piloter_graphe` n'a été codé.

- **Grammaire de hash** dans un module pur `memory-forge/app/viz/adressabilite.js`
  (`serialiser` ⇄ `analyser`, zéro import/DOM) : `focus&surligner&prof&ponts&2d`,
  défauts omis, encodage symétrique comma-safe. Couvert par 8 tests `node:test`
  (`tests/adressabilite.test.mjs`, lancés via `node.exe` — hors du harnais
  pytest, assumé) : round-trip, `focus` prime, virgule dans un nom. Servi par une
  route dédiée `GET /viz/adressabilite.js` (hors `vendor` : c'est notre code),
  sous contrat pytest.
- **Miroir parallèle** dans `index.html` : la manipulation directe (0017-0022)
  est conservée ; chaque mutation durable reflète son état dans le hash via
  `replaceState` (pas d'historique empilé, pas de `hashchange` sur nos propres
  écritures) ; un écouteur `hashchange` rejoue la navigation externe ; garde
  `appliquantHash` pendant l'application.
- **`focus` en explore-to-fetch**, `focus` prime sur `ponts`. Aspérité tranchée
  à la validation (choix utilisateur « statut + garder la vue riche ») : un
  `focus` sur entité **sans voisinage** ne détruit plus la vue — `explorer()`
  détecte le voisinage vide (`edges` vide, le backend graphiti renvoie le centre
  en **écho** et non un 404), pose un statut franc et conserve l'affichage.
  Bénéfice collatéral : la barre de recherche manuelle ne se vide plus non plus
  sur une entité inconnue.
- **Validation au réel** (navigateur, image `memory` rebuildée) : URL collée →
  vol de caméra + explore-to-fetch ; `surligner` + `2d` appliqués depuis l'URL ;
  focus vide → vue riche gardée + statut ; miroir de la manipulation directe
  (l'URL suit clics/molettes, recopiable) ; `replaceState` n'empile pas le
  curseur de seuil. Piège de session noté (`docs/impasses.md`, 2026-07-20) : une
  édition du hash ne recharge pas la page — un rebuild de l'image exige un
  rechargement forcé de l'onglet pour prendre effet.
