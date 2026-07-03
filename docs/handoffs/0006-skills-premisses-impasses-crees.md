# Handoff 0006 — Skills /premisses et /impasses créés ; LLM téléchargé ; prochaine étape : 3 modèles restants puis lancement réel

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent fait foi. En fin de session, générer le 0007 via `/handoff`.

Date : 2026-07-03 · Remplace le 0005. Session couverte : grilling complet puis création des skills `/premisses` et `/impasses`, récupération de `/delegate` depuis le `.claude` Windows, mise en place du LLM (déjà téléchargé par l'utilisateur). **Rien n'est commité par l'agent** ; commande de commit fournie à l'utilisateur (CLAUDE.md modifié + `docs/impasses.md` nouveau).

## Lire avant tout (fait autorité)

- `CLAUDE.md` (enrichi : réflexes /premisses et /impasses dans la méthode) · `CONTEXT.md` · `docs/adr/0001..0008` · `docs/ACCEPTANCE*.md`
- **`docs/impasses.md` (nouveau)** — registre du savoir négatif ; le consulter avant tout diagnostic.
- READMEs racine et par composant · Clone lecture seule OpenWebUI v0.10.2 : `/home/ftk/openwebui/`.

## État du dépôt et de l'environnement

**Code inchangé** : voice-assistant v1 + les 5 forges (memory 28 tests, world 20, time 28, host-bridge 14) — codés, **jamais exécutés en réel** ; adaptateurs réels non validés (cf. CLAUDE.md § État particulier).

**Nouveau cette session :**

- **LLM en place** : l'utilisateur a téléchargé un GGUF de ~20 Go, déplacé et renommé en `models/llm/qwen3.6-35b-a3b-q4_k_m.gguf` (nom attendu par le compose). C'est la variante **Qwen3.6-35B-A3B-Uncensored-HauhauCS-Aggressive Q4_K_M** (choix validé par l'utilisateur), pas le Qwen officiel d'unsloth du script — adapter `scripts/download-models.sh` pour qu'il **saute le LLM** s'il est présent.
- **Skills créés (globaux, `~/.claude/skills/`)** après grilling complet (8 questions, toutes décisions validées) : `/premisses` (audit extraire/trier/vérifier, statuts `vérifié ✓ / réfuté ✗ / assumé ~ / différé ⏳` avec échéance nommée, sortie éphémère, lit les impasses périmées) et `/impasses` (capture à chaud 3 champs — Tenté / Pourquoi c'est mort / **Valide tant que** —, péremption par condition explicite jamais par âge, contrainte permanente → ADR/CLAUDE.md). Données par projet : `docs/impasses.md` versionné.
- **Références croisées ajoutées** (une ligne chacune) dans `/handoff`, `/diagnosing-bugs`, `/delegate` § 3 (auditer les prémisses d'un brief avant de le figer) et CLAUDE.md.
- **`/delegate` récupéré** : il vivait dans `/mnt/c/Users/ftk/.claude/skills/` (session précédente côté Windows), copié dans `~/.claude/skills/delegate/`. Leçon : **les `.claude` Windows et WSL sont deux mondes** — si un skill mentionné par un handoff manque, regarder de l'autre côté avant de conclure qu'il n'existe pas.
- `.gitignore` : ne pas y ajouter les modèles à la racine — `models/` est déjà ignoré ; un `echo >` accidentel l'avait écrasé, restauré depuis HEAD.

## Reprendre ici

1. **Corriger `scripts/download-models.sh`** — voir l'impasse du 2026-07-02 dans `docs/impasses.md` (noms HF changés, les 4 dépôts suspects). Re-lister d'abord les vrais noms (API HF ou `--dry-run`, quelques Ko — accepté par l'utilisateur ce jour). Faire sauter le LLM (présent) ; restent **Voxtral (~3 Go), Chatterbox (~3 Go), bge-m3 (~600 Mo)** — téléchargement refusé cette session (connexion), à relancer un jour de bonne connexion avec accord explicite.
2. **Premier lancement réel** : checklist détaillée au handoff 0004 § « Reprendre ici » (points 1 à 5 : Docker Desktop/WSL, `_RealChatterboxEngine`, `GraphitiMemory` + `neighborhood`, compose + config OpenWebUI, scénarios d'acceptation) — toujours intégralement d'actualité, y ajouter le pull de l'image searxng (0005).

**Prémisses différées (échéance : premier lancement réel)** : schéma Cypher de GraphitiMemory (labels/propriétés supposés), qualité du JSON structuré produit par le 35B Uncensored pour l'extraction Graphiti (risque identifié au grilling des capacités ; si ça déçoit, re-grillinger le choix du moteur — et la variante Uncensored est un paramètre de plus à observer), adaptateurs réels jamais exécutés.

## Méthode de travail (inchangée, dans CLAUDE.md)

Analyser → proposer → **attendre validation** → TDD → tests → doc. Tout en français. Jamais de `git commit` (et **jamais de Co-Authored-By dans les messages proposés** — mémoire persistante `pas-de-co-authored-by.md`). Pas de téléchargement > 100 Mo sans accord. Nouveaux réflexes : `/premisses` avant toute tâche significative, `/impasses` à chaud.

## Suggested skills

- `/premisses` — à lancer en tout début de session prochaine (les croyances de ce handoff se vérifient, ne se croient pas — il inclura l'impasse HF périmable).
- `/verify` ou `/run` — premier lancement réel de la stack, une fois les 3 modèles téléchargés.
- `/delegate` — pour toute implémentation volumineuse (désormais présent côté WSL).
- `/handoff` — générer le 0007 en fin de session.
