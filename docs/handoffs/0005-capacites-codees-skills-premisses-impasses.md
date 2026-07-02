# Handoff 0005 — Phases 3-6 codées ; prochaine étape : griller et créer les skills /premisses et /impasses

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent fait foi. En fin de session, générer le 0006 via `/handoff`.

Date : 2026-07-02 · Remplace le 0004. Session couverte : grilling des nouvelles capacités, codage des composants world-forge / time-forge / host-bridge, création de `CLAUDE.md` et du skill `/delegate` — toujours **sans téléchargement lourd** et **rien n'est commité** (l'utilisateur commite lui-même ; `git status` : 3 modifiés, 6 nouveaux dossiers/fichiers).

## Lire avant tout (fait autorité)

- **`CLAUDE.md` (nouveau)** — les conventions du dépôt, enfin stables ; c'est ce que `/delegate` lit pour ses briefs.
- `CONTEXT.md` (glossaire enrichi : Souveraineté, phases 4-6, Pont hôte, Time/World Forge) · `docs/adr/0001..0008` · `docs/ACCEPTANCE*.md` (dont le nouveau `ACCEPTANCE-CAPACITES.md`)
- READMEs : racine (sections + « Reste à faire » complétés) et un par composant.
- Clone lecture seule OpenWebUI v0.10.2 : `/home/ftk/openwebui/`.

## État du dépôt

**Inchangé** : voice-assistant v1 et Memory Forge (5 phases, 28 tests) — codés, **jamais exécutés en réel** (modèles non téléchargés, cf. « jour de bonne connexion » au 0004, toujours d'actualité : corriger `scripts/download-models.sh`, les noms de fichiers HF ont changé).

**Nouveau cette session — 62 tests verts, ruff propre, `docker compose config` OK :**

- **Grilling des capacités** → décisions actées : souveraineté plutôt qu'isolement (ADR 0007) ; actions en liste blanche uniquement, cible bureau **Windows+WSL** (cet Ubuntu est temporaire) ; agenda local neuf, un seul monde (le Rappel = événement d'agenda) ; monde extérieur au format vocal. Ordre : Monde ext. → Quotidien+Agenda → Actions.
- **`world-forge/`** (8300, 20 tests) — MCP `web_search` (réponse sourcée via SearXNG), `weather` (Open-Meteo), `briefing` (RSS stdlib), `read_page`. `RealWorld` jamais exécuté.
- **`time-forge/`** (8400, 28 tests) — agenda SQLite, minuteurs asyncio à la seconde, boucle d'annonces avec préavis ; `POST /announce` pour smoke-test. `HostBridgeAnnouncer` (TTS Voice Forge → wav → Pont hôte) jamais exécuté.
- **`host-bridge/`** (8500, 14 tests, **hors Docker**, ADR 0008) — joue les annonces (winsound/aplay) et n'exécute que `catalog.toml` (argv explicite, jamais shell). `catalog.example.toml` fourni. `SubprocessRunner`/`SystemPlayer` jamais exécutés.
- **Compose** : services `searxng` (+ `searxng/settings.yml`, format json activé, secret_key à changer), `world`, `time` (TZ Europe/Paris, `host.docker.internal:host-gateway`). Image searxng à puller au jour de bonne connexion.
- **Skill `/delegate`** (`~/.claude/skills/delegate/`) — déléguer les implémentations volumineuses (grille haiku→sonnet→opus annoncée), brief depuis le CLAUDE.md (gabarit `BRIEF.md`), vérification adaptative par l'agent principal, échec structurel renvoyé au même subagent via SendMessage. Appliqué avec succès sur host-bridge+compose+docs cette session. Mémoire persistante associée : `deleguer-aux-subagents-opus.md`.

## Reprendre ici : griller puis créer les skills /premisses et /impasses

L'utilisateur a validé l'exploration de deux skills conçus en session (ses mots : « ta proposition de skill prémisse est très intéressante, on va explorer cela »). **Commencer par une session `/grill-me` pour les définir précisément avant d'écrire quoi que ce soit** (via `/write-a-skill` ensuite). Les concepts tels que présentés et acceptés :

**`/premisses` — audit des prémisses avant toute tâche significative.** Motivation : la faiblesse de l'agent n'est pas le code mais les croyances gelées (exemples vécus : handoff disait WSL / machine réelle Ubuntu GNOME ; noms de fichiers HF changés ; Cypher de GraphitiMemory écrit contre un schéma supposé). Les 3 mouvements : (1) **extraire** les prémisses invisibles (« ce fichier existe », « la doc est encore vraie », « l'env correspond ») ; (2) **trier** par coût-si-faux × facilité de vérification ; (3) **vérifier** le haut du tableau à bas coût (`ls`, `grep`, `--dry-run`, requête de quelques Ko) et **déclarer** le reste comme assumé. Sortie : la liste courte des croyances avec statut, pas du code.

**`/impasses` — registre du savoir négatif tactique** (nom validé ; alternatives évoquées : /cicatrices, /terrain-mine). Les 3 mouvements : (1) **capturer au moment de l'échec** (pas en fin de session) dans `docs/impasses.md` : quoi tenté, pourquoi ça ne marche pas, conditions de validité ; (2) **consulter avant d'explorer** : annoncer les mines connues avant un diagnostic ; (3) **dater et périmer** (« vrai pour OpenWebUI v0.10.2 ») — une impasse ancienne redevient une prémisse à re-vérifier. Distinction actée : les ADR gardent les alternatives *architecturales* froides ; /impasses garde le savoir *chaud*, taille une ligne.

**Points d'intégration à traiter au grilling** (demande explicite de l'utilisateur : « qu'il intègre les autres ») :

- `/premisses` × `/delegate` : auditer les prémisses d'un brief avant de le figer.
- `/premisses` × le « jour de bonne connexion » : ce rituel *est* une vérification de prémisses (noms HF, schéma Graphiti, JSON du 35B).
- `/impasses` × `/premisses` : la péremption d'une impasse la transforme en prémisse à re-tester — définir la frontière (un seul skill ? deux ? un fichier partagé ?).
- `/impasses` × `/handoff` et `/diagnose` : le handoff capture l'état, pas le négatif ; /diagnose est le principal producteur d'impasses.
- Questions ouvertes : skills génériques (`~/.claude/skills`) ou par projet ? `docs/impasses.md` versionné dans le dépôt ? Déclenchement automatique (hook ?) ou sur invocation ? Naissent-ils ensemble ou /premisses d'abord ?

## Méthode de travail exigée (inchangée, désormais dans CLAUDE.md)

Analyser → proposer → **attendre validation** → TDD → tests → doc. Tout en français. Zéro fork OpenWebUI. Jamais de `git commit`. Pas de téléchargement > 100 Mo sans accord. Implémentations volumineuses via `/delegate` (subagent au modèle adapté + vérification finale soi-même).

## Suggested skills

- `/grill-me` — définir /premisses et /impasses (l'étape qui reste, la faire en premier).
- `/write-a-skill` — les construire une fois grillés.
- `/delegate` — pour toute implémentation volumineuse (lire sa grille avant).
- `/verify` ou `/run` — premier lancement réel de la stack (toujours en attente du jour de bonne connexion, checklist au 0004 § « Reprendre ici » et README racine).
- `/handoff` — générer le 0006 en fin de session.
