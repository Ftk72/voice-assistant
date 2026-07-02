# ADR 0005 — Graphiti + Neo4j pour la mémoire persistante en graphe

Date : 2026-07-02 · Statut : accepté

## Contexte

Phase 2 du projet : une mémoire persistante unifiant deux sources — souvenirs conversationnels (extraits des conversations vocales) et connaissances documentaires (markdown + PDF) — dans **un seul graphe** d'entités, avec provenance et gestion de l'obsolescence (« Léa arrête le judo » doit invalider « Léa fait du judo » sans effacer l'historique). Visualisation navigable exigée. Tout en local, sans fork d'OpenWebUI.

## Décision

**Graphiti** (graphiti-core, embarqué dans un service custom « Memory Forge ») sur **Neo4j Community**, avec :

- extraction **différée** sur le Qwen3.6-35B existant (jobs en fin de conversation, mis en file) — jamais pendant une conversation vocale, pour préserver la cible de latence ≤ 2 s ;
- embeddings **bge-m3 sur CPU** (llama.cpp), pour ne pas entamer la marge VRAM de l'ADR 0004 ;
- intégration OpenWebUI par mécanismes natifs : Function Filter (injection en `inlet`, capture en `outlet`) + client MCP natif pour `recall`/`forget`.

## Justification

- Le modèle **bi-temporel** de Graphiti (période de validité par fait, invalidation par contradiction) est exactement l'exigence d'obsolescence — c'est le problème dur qu'on ne veut pas réécrire, avec la résolution d'entités.
- Conçu pour l'ingestion **incrémentale** (épisodes), contrairement aux pipelines GraphRAG batch.
- Neo4j apporte une visualisation navigable immédiate (Neo4j Browser) et le Cypher standard sur lequel bâtir la visualisation custom ; la RAM (64 Go) n'est pas la contrainte.

## Alternatives écartées

- **Cognee** : excellent versant corpus documentaire et plus léger (stores embarqués), mais temporalité/obsolescence des souvenirs non native ; benchmarks favorables auto-publiés.
- **LightRAG / MS GraphRAG** : indexation batch de corpus statiques — mauvais fit pour la mémoire conversationnelle incrémentale.
- **Mémoire native OpenWebUI (memories.py)** : simple liste de faits par utilisateur, ni graphe, ni temporalité, ni documents.
- **Custom complet** : résolution d'entités + invalidation temporelle = problèmes durs déjà résolus par Graphiti.
- **FalkorDB** (backend) : plus léger, mais écosystème plus étroit et Cypher partiel — Neo4j retenu pour la visualisation et l'outillage.
