---
label: wayfinder:prototype
statut: clos
assigne: claude (session 2026-07-18, implémentation déléguée sonnet)
bloque-par: [0017-somptuosite-3d-et-balade-fluide]
carte: carte-graphe-memoire
---

# Sujets dominants nommés

## Question

Chaque communauté reçoit un **nom** (« Famille », « Projet maison »…) et les
sujets se hiérarchisent. À trancher puis livrer :

- **comment nommer** : top-N des entités centrales de la communauté (gratuit,
  déterministe) vs libellé généré par le LLM local (plus juste, plus cher) —
  ou l'un en défaut, l'autre en raffinement ;
- **où l'afficher** : légende latérale cliquable (le clic vole vers la
  communauté ?), étiquettes de cluster flottant dans la scène, ou les deux ;
- côté serveur : extension d'`analyse.py` (TDD) pour exposer le nommage.

## Résolution

**Tranché et livré le 2026-07-18** (implémentation déléguée à sonnet, vérifiée
par l'agent principal) :

- **Nommage** : déterministe et gratuit, pas de LLM (réservé à « Insight en
  français du LLM local », 0020) — les 3 entités les plus centrales de chaque
  communauté, jointes par ` · ` (ex. `"Léa Fontaine · Judo · Karaté"`) ;
  égalité de centralité départagée alphabétiquement pour rester reproductible.
  Nouvelle fonction `nommer_communautes()` dans
  [analyse.py](../../../memory-forge/app/viz/analyse.py), testée (4 tests :
  ordre par centralité, communauté à 1 membre, déterminisme sur égalité,
  communautés distinctes) ; exposée par `GET /graph/complet` via un nouveau
  champ `noms_communautes` sur `GrapheComplet`.
- **Affichage** : légende latérale cliquable dans `<aside>` (pas d'étiquettes
  flottantes en 3D — complexité de positionnement non justifiée pour ce lot),
  triée par taille de communauté décroissante ; le clic vole vers l'entité la
  plus centrale de la communauté (réutilise `volerVers`) et verrouille le
  focus dessus comme un clic sur le nœud.
- **Hors périmètre confirmé** : la légende ne se met pas à jour lors d'une
  exploration ciblée (`GET /graph` ne porte pas `noms_communautes`) — elle
  reste celle du dernier chargement du graphe complet.
- Vérifié : `uv run pytest` (81 passed — 6 erreurs `test_openwebui_filter.py`
  préexistantes, hors sujet, cf. ticket 0016) et `uv run ruff check .` verts.
  Jugement visuel de la légende encore à faire par l'utilisateur au réel.
