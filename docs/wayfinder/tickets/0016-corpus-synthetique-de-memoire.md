---
label: wayfinder:task
statut: clos
assigne: claude (session 2026-07-18)
bloque-par: []
carte: carte-graphe-memoire
---

# Corpus synthétique de mémoire

## Question

Fabriquer et injecter dans memory-forge un graphe synthétique dense qui rendra
tous les tickets suivants jugeables à l'œil, en couvrant délibérément les cas
limites qu'un corpus réel ne garantit pas :

- plusieurs communautés de tailles contrastées (une géante, des moyennes, une
  minuscule) ;
- des entités-ponts reliant des communautés, et des paires de communautés
  quasi déconnectées (futurs « trous ») ;
- des nœuds isolés, des noms longs et accentués, des faits obsolètes en masse
  (`invalid_at`), les deux provenances (conversation, document).

Décisions internes au ticket : voie d'injection (API d'ingestion memory-forge
vs Cypher direct dans Neo4j — la première exerce la vraie chaîne, la seconde
maîtrise exactement la topologie), volume cible (plusieurs centaines
d'entités), et rejouabilité (script versionné, graphe régénérable après purge).

## Résolution

**Livré et validé au réel le 2026-07-18** : 264 entités et 555 faits
synthétiques en place dans Neo4j, servis par `/graph/complet` (268 nœuds avec
les 4 réels, 14 communautés Louvain aux tailles contrastées 132→1, 97 faits
obsolètes, deux provenances, hubs émergés — « Projet Héliotrope » centralité
1.0 — ponts présents).

- **Voie d'injection : Cypher direct**, actée — l'API `/episodes` passe par
  l'extraction LLM (non déterministe, topologie ingarantissable) ; la viz ne
  lit que `Entity`/`RELATES_TO`/`Episodic`, écrits tels quels. Contrepartie
  assumée : pas d'embeddings ni de fulltext → `/search` ignore le synthétique,
  seule la viz le voit.
- **Générateur pur et testé** :
  [scripts/corpus_synthetique.py](../../../memory-forge/scripts/corpus_synthetique.py)
  et [tests/test_corpus_synthetique.py](../../../memory-forge/tests/test_corpus_synthetique.py)
  (13 tests = le contrat des cas limites : géante 110 / minuscule 3, 3 ponts
  nommés dont « Léa Fontaine relie Travail et Musique », trou structurel
  Voyages↔Sport ≤ 1 arête, « Jeux de rôle » rattaché par un seul fil, 6 nœuds
  isolés, 3 noms à rallonge accentués, « Appartement de Lyon » tout obsolète,
  déterminisme par graine).
- **Rejouable et réversible** : chaque nœud porte `corpus: "synthetique"` ;
  le script purge-puis-recrée (idempotent). Depuis WSL,
  `~/voice-assistant/memory-forge` :
  `set -a && . ../.env && set +a && uv run python -m scripts.corpus_synthetique`
  (ajouter `--purger` pour rendre la mémoire réelle seule).
- **Faits annexes** : image Docker `memory` rebuildée (elle ne servait pas
  encore les routes viz — reliquat tracé à « Expérience déménagement ») ;
  driver `neo4j` ajouté au groupe dev de memory-forge ;
  `tests/test_openwebui_filter.py` est un reliquat du ménage (vise un fichier
  purgé, 6 erreurs pytest) — **à supprimer par l'utilisateur**.
