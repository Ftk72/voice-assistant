# documents/ — ingestion documentaire du Memory Forge

Déposer ici les documents à mémoriser (`.md`, `.pdf`). Le service `memory` surveille
ce dossier (polling ~10 s) et intègre chaque document au graphe : markdown découpé
par sections, PDF par page. Un fichier modifié est ré-ingéré ; la résolution des
contradictions revient au moteur du graphe (ADR 0005).

Le fichier `.memory-forge-state.json` est l'état du watcher (mtime par fichier) —
ne pas le versionner ni l'éditer. Le supprimer force une ré-ingestion complète.
