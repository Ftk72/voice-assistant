---
label: wayfinder:task
statut: clos
assigne: subagent-sonnet (délégation du 2026-07-10, session carte)
bloque-par: []
---

# Ménage du dépôt

## Question

Purger le legacy OpenWebUI et remettre le dépôt au carré (AFK, délégable) :

- **Supprimer** : `openwebui/` (functions), `coturn/` + service compose
  (dormant depuis la co-localisation Windows — l'historique git le garde),
  `stt/template-transcription.jinja` (template « greffier » de l'ère Voxtral ;
  `stt/Dockerfile` whisper.cpp sm_120 **reste**, il est la stack actuelle),
  `docker-compose.sans-stt.yml` si son seul sens était Voxtral.
- **Compose v2** : retirer les services `openwebui` et `coturn`, le volume
  `open-webui-data` et toutes les variables `RAG_*`/`OFFLINE_MODE` liées ;
  garder llm, stt, voice-forge, embedder, memory, searxng, world, time,
  dialogue. Vérifier que rien ne référence plus les services retirés.
- **`.gitignore`** : ajouter `host-bridge/catalog.toml` (config personnelle —
  `catalog.example.toml` reste versionné, cf. git status permanent).
- **`scripts/`** : réaligner (download-models.sh sans Voxtral si le swap
  whisper est consommé, smoke-tests pointés sur la stack actuelle,
  demarrage-hote.sh relu).
- Critère de clôture : `docker compose config` valide, `uv run pytest` et
  `ruff check .` verts dans chaque forge touchée, plus aucune occurrence
  d'openwebui/coturn/Voxtral hors `docs/` (ADR, impasses et handoffs sont
  l'histoire — ils ne se réécrivent pas).

## Résolution (2026-07-10, vérifiée par l'agent principal)

Livré et vérifié (diff conforme, `docker compose config -q` OK, `bash -n` OK,
zéro occurrence openwebui/coturn/voxtral hors docs) : `openwebui/` et
`coturn/` supprimés, compose v2 (services et volume morts retirés),
`docker-compose.sans-stt.yml` supprimé (ses deux prémisses — openwebui et
modèle Voxtral absent — sont mortes), `stt/template-transcription.jinja`
était en réalité un dossier vide orphelin (artefact Docker) supprimé,
`.gitignore` ignore `host-bridge/catalog.toml`, scripts réalignés (le swap
whisper était déjà consommé : `ggml-large-v3-turbo-q5_0.bin`).

Suites traitées dans la foulée par l'agent principal :
- `transport-voix/app/config.py` pointait encore le coturn supprimé
  (`turn_url` par défaut) → défaut vidé (co-localisation Windows, media en
  localhost sans relais), tests verts.
- Les conteneurs orphelins `openwebui` et `coturn` tournent encore ; à purger
  après la session de test : `docker compose up -d --remove-orphans`.
