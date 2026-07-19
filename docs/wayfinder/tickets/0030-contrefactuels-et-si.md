---
label: wayfinder:prototype
statut: clos
assigne: session-2026-07-20
bloque-par: []
carte: carte-graphe-memoire
---

# Contrefactuels « et si ? »

## Question

Gradué au grilling du 2026-07-18 (recherche SOTA versée le même jour) :
manipuler le graphe en mode **« et si ? »** — masquer visuellement une entité
ou une arête et voir l'analyse se recalculer (communautés, ponts, trous,
insight), pour comprendre **ce qui tient à quoi** dans la mémoire. Famille de
recherche : perturbation minimale → dérive observée
([CFFTLLMExplainer](https://arxiv.org/abs/2509.21241),
[LLM Analyzer](https://arxiv.org/abs/2405.00708)).

Prototype HITL (/prototype, l'utilisateur juge à l'œil dans `/viz`) :

- **Le geste** : comment on masque (clic sur nœud/arête en mode « et si »,
  panier de masques cumulables, bouton retour au réel ?) — le masque est
  **éphémère et purement visuel/analytique**, jamais écrit en base (la
  correction durable, c'est 0029).
- **Le recalcul** : Louvain, ponts et trous se recalculent côté serveur sur le
  sous-graphe masqué (`analyse.py` prend-il un filtre ?) ; l'insight LLM
  est-il rejoué à chaque masque ou à la demande (9 s en régime — trop lent
  pour du temps réel) ?
- **La lisibilité** : comment montrer *ce qui a changé* (communautés
  re-colorées ? diff avant/après ? les nœuds orphelins créés par le
  masque ?) sans perdre l'utilisateur.

Jouable au navigateur sur le corpus synthétique — indépendant de la séance de
validation (0024). Dernier des trois chantiers du grilling (transparence →
correction → contrefactuels) : le plus spectaculaire, mais valeur à confirmer
au prototype.

## Critère de clôture

Un mode « et si ? » jugé à l'œil par l'utilisateur et livré (ou renoncement
argumenté consigné) — masques éphémères, recalcul serveur, retour au réel
en un geste.

## Résolution

**Livré et validé à l'œil le 2026-07-20** (délégué sonnet). Les trois
questions du ticket, tranchées au prototype :

- **Le geste** : case « et si ? » dans l'en-tête de `/viz` ; en mode actif,
  clic nœud = masque l'entité, clic arête = masque le fait (si porteur
  d'uuid) ; panier de puces cumulables (✕ par masque) dans une section
  latérale dédiée, « Retour au réel » vide le panier en un geste, décocher la
  case sort du mode et recharge le réel. Rien n'est jamais écrit en base.
- **Le recalcul** : `POST /et-si` (lecture seule) — `masquer()` (fonction
  pure d'`analyse.py`) filtre la tranche des 500 nœuds les plus connectés,
  puis ré-enrichissement complet sur le sous-graphe (communautés, centralité,
  noms, condensé). L'insight LLM n'est **pas** rejoué (9 s, trop lent pour un
  geste interactif) : le diff déterministe des condensés suffit — le bouton
  insight est désactivé pendant le mode.
- **La lisibilité** : recoloration automatique par les nouvelles communautés
  (le rendu suit `noms_communautes` du sous-graphe), diff textuel
  `condense_reel` vs `condense_masque` (sujets avant → après, ponts et trous
  disparus/apparus, entités isolées) ; les orphelins créés par le masque
  **restent en scène** (exception au filtre de `rafraichir()`), ils sont ce
  qu'on veut voir.

7 tests ajoutés (174 au total, verts), dont la preuve de non-écriture
(`GET /graph/complet` intact après un `POST /et-si`). Clôt le dernier des
trois chantiers du grilling killer features (transparence → correction →
contrefactuels).
