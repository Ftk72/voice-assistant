---
label: wayfinder:prototype
statut: clos
assigne: claude (session 2026-07-18)
bloque-par: [0019-ponts-entre-communautes]
carte: carte-graphe-memoire
---

# Insight en français du LLM local

## Question

Le graphe **parle** : un paragraphe en français, généré par le LLM local,
résume ce que la mémoire sait, ses sujets, ses ponts — la valeur « outil »
d'InfraNodus. À trancher puis livrer :

- **flux** : memory-forge appelle llama.cpp (port 8001) directement, ou passe
  par Dialogue Forge ? (memory-forge n'a aujourd'hui aucun client LLM — port
  ABC + adaptateur factice à créer, pattern maison) ;
- **matière première** : quel condensé du graphe envoyer au LLM (sujets
  nommés, ponts, statistiques — pas le graphe brut) ;
- **où et quand** : panneau dédié, génération à la demande (bouton) vs
  automatique ; coût/latence acceptables ;
- la description MCP éventuelle reste orientée voix.

## Résolution

Tranché (validé par l'utilisateur) puis livré le 2026-07-18 (délégué sonnet,
vérifié et smoke-testé par l'agent principal) :

- **Flux** : appel **direct llama.cpp** (`llm:8080/v1`, réglage `llm_base_url`
  déjà présent) — passer par Dialogue Forge aurait inversé le sens des
  dépendances. Pattern maison : port ABC `GenerateurInsight`
  (`app/insight/base.py`) + factice (défaut, testé) + réel OpenAI-compat
  (`openai_compat.py`, httpx, timeout 120 s), factory dans `main.py`,
  `MEMORY_FORGE_INSIGHT_BACKEND` (compose : `openai`).
- **Matière première** : un `CondenseGraphe` calculé serveur
  (`condenser()` dans `analyse.py`, TDD) — sujets nommés triés par taille,
  entités-ponts (≥ 2 communautés touchées, top 5 déterministe, définition du
  ticket 0019), stats (entités, faits, obsolètes). Jamais le graphe brut.
  Prompt français pur et testable (`prompt.py`) : un seul paragraphe, ton
  oral, aucun chiffre inventé.
- **Où et quand** : panneau « Insight » en tête de l'aside de `/viz`,
  génération **à la demande** (bouton « Raconter la mémoire »), état
  d'attente honnête, erreurs affichées. Pas d'automatique.
- **MCP** : outil `raconter_memoire` (sans argument), description orientée
  voix, même service partagé que la route `GET /insight`
  (`app/insight/__init__.py`).
- **Smoke-test réel** (WSL → port debug 8001, condensé de démonstration) :
  paragraphe français fidèle au condensé, **93 s au premier appel**
  (chargement des poids — bien au-delà des 41 s documentés), **9,1 s en
  régime**. L'adaptateur réel n'est plus « jamais exécuté ».
- Reste dû (HITL) : jugement visuel de l'utilisateur dans `/viz` après
  rebuild de l'image `memory`, et test voix de `raconter_memoire` via
  Dialogue Forge (redémarré pour voir le nouvel outil).
