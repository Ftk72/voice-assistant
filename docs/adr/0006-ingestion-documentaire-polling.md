# ADR 0006 — Ingestion documentaire : dossier surveillé par polling mtime

Date : 2026-07-02 · Statut : accepté

## Contexte

Phase 4 du Memory Forge (scénario « croisement » d'ACCEPTANCE-MEMOIRE.md) : les
documents déposés dans `documents/` doivent rejoindre le même graphe que les
souvenirs conversationnels, sans autre geste que le dépôt du fichier. La stack
tourne sous WSL2 avec des bind-mounts Docker.

## Décision

- **Dossier `documents/` à la racine** (pattern de `voices/`), monté en
  lecture-écriture dans le service `memory`.
- **Watcher par polling mtime (~10 s, configurable)** dans le Memory Forge,
  état persisté dans `documents/.memory-forge-state.json` (mtime par fichier).
- **Découpage** : markdown par sections (un épisode par titre), PDF par page
  (`pypdf`, pur Python ~2 Mo). Un épisode = un fragment de document (CONTEXT.md).
- **Ré-ingestion naïve** : fichier modifié → re-découpage et ré-ingestion
  complète ; la résolution des contradictions/doublons est déléguée au moteur
  du graphe (Graphiti, ADR 0005).
- Les épisodes documentaires rejoignent la **même file d'extraction différée**
  que les conversations (jamais d'extraction pendant une conversation vocale).

## Justification

- inotify ne remonte pas les événements de l'hôte à travers les bind-mounts
  WSL/Docker ; le polling mtime est le seul mécanisme fiable ici, et 10 s
  suffisent largement pour un dépôt manuel de fichiers.
- L'état sur disque survit aux redémarrages du conteneur : pas de ré-ingestion
  au boot. Supprimer le fichier d'état force une ré-ingestion complète (outil
  de réparation assumé).
- Le diff fin par section modifiée serait complexe pour un gain marginal :
  Graphiti gère déjà entités existantes et faits contredits.

## Alternatives écartées

- **inotify/watchdog** : cassé sur bind-mounts WSL — cause de bugs silencieux.
- **Endpoint d'upload** : geste supplémentaire, contraire au « je dépose un
  fichier » du scénario d'acceptation ; l'API `POST /episodes` reste disponible.
- **Extraction PDF riche (unstructured, PyMuPDF)** : dépendances lourdes ou non
  pur-Python ; `pypdf` suffit pour du texte, à réévaluer si des PDF scannés
  apparaissent.
