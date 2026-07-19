---
label: cerp:observe
ticket: 0036-cerp-observer-le-depot
cree: 2026-07-19
---

# CERP — Observations du dépôt (phase Observe, ticket 0036)

> **Nature du document.** Collecte d'évidence brute pour la reconstruction du
> CIR (ticket 0038). Ce n'est ni une doc du produit ni un jugement de qualité :
> ce sont des **faits sourcés** sur la manière de décider de l'auteur.
> Discipline (carte-cerp) : observations et interprétations strictement
> séparées ; chaque observation porte une source (chemin, ligne, ou hash de
> commit) ; les **absences** comptent autant que les patterns.
> Portée : le dépôt seul. La couche méta (`~/.claude/skills`, mémoire agent)
> relève du ticket 0037, traité par ailleurs.
> État observé : commit de tête `f6962fb` (2026-07-18) + arbre de travail avec
> modifications non commitées et fichiers non suivis (voir §7).

---

## 1. Faits de surface : périmètre, auteur, cadence

- **O-1.1** Le dépôt compte 57 commits, du 2026-07-02 (`4ed1fde first commit`
  puis `14ac4a4`) au 2026-07-18 (`f6962fb`). Source : `git rev-list --count`,
  `git log`.
- **O-1.2** Auteur quasi unique : `ftk <ftk72hotmail.com@gmail.com>` (55
  commits) ; 2 commits sous `Ftk72 <…@users.noreply.github.com>` (même
  personne, identité GitHub web). Source : `git log --format='%an <%ae>'`.
- **O-1.3** Aucun commit ne porte de trailer `Co-Authored-By`. Source :
  `git log --format='%b' | grep -c Co-Authored` → 0. Concordant avec la
  mémoire agent « Pas de Co-Authored-By » et le retrait de la signature Claude.
- **O-1.4** Cadence en salves sur ~9 jours actifs : 4/4/12/3/10/5/6/6/7 commits
  aux dates 07-02, 07-03, 07-06, 07-07, 07-08, 07-09, 07-16, 07-17, 07-18. Trou
  du 07-10 au 07-15 (aucun commit). Source : `git log --date=short`.
- **O-1.5** Le travail est daté au-delà des commits : les docs référencent des
  sessions jusqu'au **2026-07-19** (ADR 0013, carte-cerp, carte-action-forge,
  handoff 0018) — non commitées (§7). Source : dates en tête de ces fichiers.
- **O-1.6** Composants présents (répertoires de premier niveau) : `dialogue-forge/`,
  `voice-forge/`, `memory-forge/`, `world-forge/` (absent de l'arbre — voir
  O-1.7), `time-forge/`, `host-bridge/`, `transport-voix/`, `coquille/`,
  `stt/`, `personas/`, `docs/`, `models/`, `documents/`, `scripts/`. Source :
  listing racine.
- **O-1.7** `world-forge/` est nommé partout (CLAUDE.md, CONTEXT.md, ADR 0007,
  compose) mais **n'apparaît pas** dans l'arbre de fichiers listé ni comme
  service bâti ; `stt/` ne contient qu'un `Dockerfile` (pas de forge Python).
  Source : listing complet des fichiers. (Voir §6, absences.)

## 2. Patterns d'architecture (récurrents)

- **O-2.1 — Port ABC + adaptateur factice + adaptateur réel.** Chaque capacité
  externe est un port ABC dans `app/<domaine>/base.py`, un `fake.py` sans
  réseau ni matériel (défaut, utilisé par les tests), et un adaptateur réel
  séparé. Exemples : `dialogue-forge/app/llm/{base,fake,openai_compat}.py`,
  `.../memoire/{base,fake,rest}.py`, `.../voix/{base,fake,rest}.py`,
  `.../outils/{base,fake,mcp}.py` ; `memory-forge/app/graph/{base,fake,graphiti}.py`,
  `.../insight/{base,fake,openai_compat}.py` ; `host-bridge/app/actions/{base,fake,subprocess_runner}.py`,
  `.../audio/{base,fake,system}.py`. Le pattern est explicité dans CLAUDE.md
  §Conventions des forges.
- **O-2.2 — Factories + sélection par Settings.** `create_app(settings)` dans
  `app/main.py` construit chaque port via un `build_<x>(settings)` qui teste
  `settings.<x>_backend` et importe l'adaptateur réel *à la demande* (import
  local dans la branche), défaut = factice. Source :
  `dialogue-forge/app/main.py` L24-52.
- **O-2.3 — FastAPI, contrat homogène.** `/health` → `{"status":"ok"}`,
  lifespan pour init/fermeture, MCP monté sur `/mcp` via
  `FastMCP(..., stateless_http=True)`, `env_prefix` par composant
  (pydantic-settings). Source : CLAUDE.md ; `dialogue-forge/app/main.py` ;
  tests `test_health_repond_ok`, `test_l_endpoint_mcp_est_monte`.
- **O-2.4 — Chaque forge sert sa propre UI ; la coquille n'assemble.** Modules
  d'interface servis par leur forge : voice-forge `/admin`, memory-forge `/viz`,
  dialogue-forge `/module_dialogue` et `/reglage`, action-forge `/atelier`
  (prévu). La coquille Tauri charge ces pages en onglets/iframes, sans logique
  métier. Source : CLAUDE.md §Conventions ; ADR 0009/0010 ; carte.md ticket 0022.
- **O-2.5 — Descriptions d'outils MCP orientées voix.** Consigne récurrente
  « restitue oralement, ne lis pas la liste ». Source : CLAUDE.md ; ADR 0013
  (`confier_tache`/`etat_tache`/`annuler_tache` « le Compte rendu se restitue
  oralement, le journal ne se lit jamais »).
- **O-2.6 — Prompt à préfixe stable pour le cache LLM.** L'orchestrateur liste
  les outils une seule fois au démarrage et injecte la mémoire *en aval* du
  système, pour que le préfixe envoyé au LLM reste identique octet pour octet
  d'un tour à l'autre (cache de préfixe llama.cpp, prefill MoE lent). Source :
  `dialogue-forge/app/main.py` L64-67 ; tests
  `test_le_message_systeme_est_identique_octet_pour_octet_entre_deux_tours`,
  `test_le_bloc_de_consignes_outils_est_identique_entre_deux_personas` ;
  roadmap.md §« Prefill lent ».
- **O-2.7 — memory-forge est le composant-modèle.** « Modèle à imiter pour un
  nouveau composant : memory-forge/ » (CLAUDE.md). Les deux nouvelles forges
  décidées (action-forge, ADR 0013) se déclarent « pattern memory-forge ».
- **O-2.8 — Un seul pied hors Docker, assumé et isolé.** host-bridge est le
  seul composant natif (ADR 0008) ; il est « sans intelligence » (exécute, ne
  décide pas) et borné par liste blanche `catalog.toml` (argv, jamais un shell).
  Le même principe « sûreté par surface bornée » est reconduit à l'action-forge
  (ADR 0013 : « la garde est dans la surface de l'API, pas dans une auth »).

## 3. Patterns de nommage et de style (récurrents)

- **O-3.1 — Tout en français, sans exception constatée.** Code (identifiants,
  docstrings, commentaires), tests, docs, messages de commit. Identifiants
  métier français : `Orchestrateur`, `MoteurLLM`, `DeltaTexte`, `AppelOutil`,
  `CatalogueVoix`, `preparer_lignes`. Source : tout le code lu ; CLAUDE.md
  (« Tout est en français »).
- **O-3.2 — Tests nommés comme des phrases-assertions françaises.** Convention
  `test_<phrase>` déclarative : `test_l_episode_ne_contient_que_l_utilisateur`,
  `test_le_message_systeme_est_identique_octet_pour_octet_entre_deux_tours`,
  `test_run_action_hors_liste_blanche_refuse_sans_rien_lancer`,
  `test_les_backchannels_sont_exclus_de_l_episode`. Source : `grep def test_`
  sur tous les `tests/`. La convention est donnée en exemple dans CLAUDE.md
  (`test_le_minuteur_annonce_a_l_echeance`).
- **O-3.3 — Toolchain identique partout.** Python 3.12 borné
  `requires-python = ">=3.12,<3.13"`, uv, ruff `line-length 100` /
  `select ["E","F","I","UP","B","SIM"]`, pytest `asyncio_mode="auto"` +
  `pythonpath=["."]`. Source : `memory-forge/pyproject.toml` (identique de
  structure aux autres) ; CLAUDE.md.
- **O-3.4 — Dépendances lourdes en extra optionnel séparé.** `graphiti`
  (memory-forge), `chatterbox`/`qwen3tts` (voice-forge), `pipecat`
  (transport-voix). Commentaire type : « Extra volontairement séparé …
  Installer plus tard avec uv sync --extra … ». Extras inconciliables
  déclarés `[tool.uv] conflicts`. Source : `memory-forge/pyproject.toml`
  L15-19 ; CLAUDE.md.
- **O-3.5 — Numérotation à quatre chiffres, un fichier par artefact.** ADR
  `NNNN-slug.md`, handoffs `NNNN-slug.md`, tickets wayfinder `NNNN-slug.md`
  (numérotation unique toutes cartes confondues). Slugs en français. Source :
  listings `docs/adr/`, `docs/handoffs/`, `docs/wayfinder/tickets/`.
- **O-3.6 — Vocabulaire de domaine tenu par un glossaire canonique.** CONTEXT.md
  « fait foi pour le vocabulaire du domaine » ; il est réécrit à chaque ADR qui
  déplace le vocabulaire (ADR 0009, ADR 0011, ADR 0013). Renommages tracés
  explicitement (« Action » → « Commande du catalogue », ADR 0013 ; « mode
  appel » → « Conversation », CONTEXT.md). Source : CONTEXT.md ; ADR 0013 §Conséquences.

## 4. Rituels de documentation et de méthode (récurrents)

- **O-4.1 — Décision d'abord, code ensuite.** Séquence explicite « Analyser →
  proposer → attendre validation → coder en TDD → tests → doc » (CLAUDE.md).
  Le TDD est visible dans le code : ports factices d'abord, tests portant sur
  le comportement (`test_rien_n_est_capture_avant_la_cloture`, etc.).
- **O-4.2 — ADR pour les décisions structurantes.** 13 ADR (0001→0013), format
  fixe : `# ADR NNNN — titre`, ligne `Date : … · Statut : accepté`, sections
  Contexte / Décision / Justification|Conséquences / Alternatives écartées. Les
  ADR se **remplacent/précisent** explicitement (0003 « remplacé par 0009 »,
  0009 « remplace 0003 », 0010/0011/0012 « précise 0009 »). Source :
  `docs/adr/*.md`.
- **O-4.3 — Registre des impasses (savoir négatif tactique).** `docs/impasses.md` :
  ~20 entrées datées, format à trois champs (Tenté / Pourquoi c'est mort /
  Valide tant que), la « Valide tant que » rendant la péremption décidable. Les
  impasses périmées sont **marquées barrées** (`~~…~~ — PÉRIMÉE/LEVÉE`), jamais
  supprimées. Consigne : « consulter le registre avant tout diagnostic ».
  Source : `docs/impasses.md`.
- **O-4.4 — Handoffs numérotés, seul le dernier fait foi.** 18 handoffs
  (0001→0018). `docs/handoffs/README.md` : « Seul le dernier fait foi ». Chaque
  handoff liste État / Prémisses vérifiées / Prochaine étape / Points
  d'attention / Skills suggérés / Modifiés non commités. Source :
  `docs/handoffs/`.
- **O-4.5 — Tracker wayfinder en markdown versionné (pas d'issues GitHub).**
  « Le dépôt n'a pas de tracker d'issues accessible (gh absent) … souverain,
  comme le reste ». Cartes = index, tickets = décisions ; frontmatter
  `label/statut/assigne/bloque-par` ; « Jamais plus d'un ticket résolu par
  session ». Source : `docs/wayfinder/README.md`.
- **O-4.6 — Le « grilling » comme rite de décision.** 41 fichiers de docs
  mentionnent « grilling » ; sessions datées 07-02 (×2), 07-07, 07-08, 07-10,
  07-18, 07-19. Chaque ADR récent et chaque carte cite le grilling qui l'a
  tranché. Source : `grep -rl grilling docs/` → 41. (Le mot est **quasi absent
  des messages de commit** : 3 sur 57 — voir O-6.5.)
- **O-4.7 — « Validé au réel » comme critère de clôture.** Formule récurrente
  dans les cartes (13 occurrences carte.md, 7 carte-graphe-memoire.md) : un
  ticket n'est clos qu'après vérification sur le poste Windows réel, souvent
  « à l'oreille » pour l'audio, avec date. Source : `grep validé au réel`.
- **O-4.8 — Audit des prémisses avant toute tâche.** « les croyances des
  handoffs se vérifient, ne se croient pas » (CLAUDE.md). Les handoffs listent
  une section « Prémisses vérifiées cette session (à ne pas re-payer, mais
  périssables) ». Source : CLAUDE.md ; handoff 0018 §Prémisses.
- **O-4.9 — Distinction explicite agent / utilisateur pour les commandes.**
  Toute commande destinée à l'utilisateur suit un format `/newbie` (une fenêtre
  par bloc, environnement déclaré, bloc autonome, signe de succès). Source :
  CLAUDE.md §Méthode.

## 5. Rapport aux contraintes matérielles et aux dépendances (récurrent)

- **O-5.1 — Contrainte matérielle traitée comme un invariant premier.** RTX
  5080 = Blackwell sm_120 : « aucun binaire CUDA ne se présume compatible avant
  un test réel ». 16 Go VRAM partagés LLM+STT+TTS, budget VRAM chiffré par
  service (ADR 0004). Source : CLAUDE.md §Matériel ; ADR 0004 ; roadmap.md.
- **O-5.2 — Défiance envers les téléchargements lourds, systématisée.** « aucun
  téléchargement lourd (>100 Mo) sans accord explicite — et c'est l'utilisateur
  qui lance ». Vérification des dépôts/tags par API avant de fournir une
  commande. Plusieurs impasses portent sur des téléchargements silencieux
  (2026-07-06 RAG OpenWebUI ~1 Go ; 2026-07-18 rebuild voice-forge ~2,5 Go ;
  2026-07-17 build en cascade `depends_on`). Source : CLAUDE.md ; docs/impasses.md.
- **O-5.3 — Diagnostic par la mesure, pas par l'impression.** Récurrent dans
  les impasses : « Diagnostiquer par la mesure (un curl chronométré), jamais
  par l'impression de lenteur » ; latences chiffrées partout (STT TTFB
  0,3-0,5 s ; clone 1,75 s ; LLM 0,9 vs 33 tok/s ÷37 en pagination). Source :
  docs/impasses.md (entrées 2026-07-17, 2026-07-06).
- **O-5.4 — Conteneurisation maximale, une seule exception assumée.** Tout
  service conteneurisable l'est (compose versionné) ; host-bridge est
  l'exception, motivée par ADR 0008. Source : CLAUDE.md ; mémoire agent
  « Conteneurisation maximale » ; docker-compose.yml.
- **O-5.5 — Souveraineté reformulée, pas abandonnée.** « 100 % souverain »
  redéfini en ADR 0007 : modèles et données personnelles en local ; requêtes
  sortantes anonymes permises (SearXNG, météo sans clé, RSS). Les sandboxes
  cloud sont refusées « jamais » (ADR 0013). Source : ADR 0007 ; CONTEXT.md
  « Souveraineté » ; ADR 0013 §Hors périmètre.

## 6. Absences récurrentes (ce qui n'est jamais fait / jamais toléré)

- **O-6.1 — Jamais de `git commit` par l'agent.** Répété en CLAUDE.md, dans
  chaque carte, chaque handoff, la mémoire agent. « l'utilisateur commite
  lui-même ». Corroboré par O-1.2 (auteur unique = l'utilisateur).
- **O-6.2 — Jamais de fork d'OpenWebUI.** Règle « zéro fork » (ADR 0003), puis
  sortie totale d'OpenWebUI (ADR 0009). Le commit `f6962fb` et `8ef15f8`
  suppriment les derniers vestiges (filtre, functions, coturn). La mémoire
  agent porte « zéro fork OpenWebUI ». Source : ADR 0003/0009 ; commits.
- **O-6.3 — Jamais d'adaptateur réel présenté comme fonctionnel avant son
  premier run.** Convention « adaptateur réel documenté 'jamais exécuté à ce
  jour' tant qu'il n'a pas tourné » (CLAUDE.md). État particulier nomme
  nommément `SubprocessRunner` et `_RealQwen3TTSEngine` comme « jamais
  exécutés ». Source : CLAUDE.md §Ports/adaptateurs et §État particulier.
- **O-6.4 — Jamais de logique métier dans la coquille.** Répété (CLAUDE.md,
  ADR 0009/0010, CONTEXT.md). « la coquille Tauri ne fait qu'assembler ».
- **O-6.5 — Le « grilling » est quasi absent des messages de commit.**
  3 commits sur 57 le mentionnent (dans le corps : `53e7488` ADR 0009,
  `f2d8a45` ADR 0010, `bddf3d1` ADR 0011 — jamais dans le sujet), contre 41
  fichiers de docs — la délibération vit dans l'ADR/le ticket, le commit ne
  fait que l'enregistrer. Source : `git log -i --grep=grilling` ;
  `grep -rl grilling docs/ | wc -l` → 41.
- **O-6.6 — Pas de second LLM introduit pour contourner un problème.** ADR 0011
  tranche « déclaratif et déterministe plutôt qu'un second LLM (latence +
  nouvelle surface d'hallucination) » ; filtre backchannels déterministe plutôt
  qu'une passe LLM. Source : ADR 0011 §Contexte et décision 2.
- **O-6.7 — L'assistant ne fait jamais foi comme source de mémoire.** ADR 0011 :
  « L'utilisateur seul fait foi » — la parole de l'assistant n'est jamais
  ingérée (réponse à un faux fait constaté). Test
  `test_l_episode_ne_contient_que_l_utilisateur`. Source : ADR 0011 ;
  `dialogue-forge/tests/test_conversations.py`.
- **O-6.8 — Pas de commande arbitraire sur l'hôte.** host-bridge n'exécute que
  la liste blanche (jamais un shell). Reconduit à l'action-forge : l'arbitraire
  n'est permis qu'en sandbox jetable, jamais sur l'hôte. Source : ADR 0008,
  ADR 0013.
- **O-6.9 — Composants annoncés mais non encore matérialisés.** `world-forge/`
  (phase 6) et `action-forge/` (ADR 0013 du 2026-07-19) sont nommés dans les
  docs mais absents de l'arbre de code ; `stt/` se réduit à un Dockerfile
  (whisper.cpp compilé, pas de forge). Observation, sans jugement. Source :
  listing des fichiers vs CLAUDE.md/CONTEXT.md.

## 7. État de l'arbre de travail (non commité, à la date d'observation)

Signalé comme tel : `git status` montre des modifications et des fichiers non
suivis absents de l'historique. Ils reflètent des sessions postérieures au
dernier commit (jusqu'au 2026-07-19).

- **O-7.1 — 11 fichiers modifiés non commités** : `CONTEXT.md`,
  `docker-compose.yml`, `docs/impasses.md`, `docs/wayfinder/carte.md`,
  `docs/wayfinder/carte-graphe-memoire.md`,
  `docs/wayfinder/tickets/0015-…`, `personas/assistant.md`,
  `transport-voix/app/config.py`, `transport-voix/app/transport/pipecat.py`,
  `voice-forge/app/voices/manager.py`, `voice-forge/tests/test_admin_api.py`.
  Source : `git status`, `git diff --stat` (236 insertions / 69 suppressions).
- **O-7.2 — Nouveautés non suivies structurantes** : `docs/adr/0013-…`
  (nouvel ADR daté du 2026-07-19), trois nouvelles cartes wayfinder
  (`carte-action-forge.md`, `carte-cerp.md` — plus `carte-graphe-memoire.md`
  déjà présente), tickets 0023→0040, handoff 0018, `voice-forge/scripts/`,
  `voice-forge/app/voices/normalisation.py` + son test,
  `transport-voix/app/assets/`. Source : `git status`.
- **O-7.3 — Le handoff 0018 confirme le décalage** : la session du 2026-07-18
  n'a « écrit aucune ligne de code » (grilling du ticket 0029 seulement) et
  note que « de nombreux autres fichiers étaient déjà modifiés/non suivis avant
  la session ». Source : `docs/handoffs/0018-…`.

## 8. Recensement des décisions datées traçables (évidence pour le CIR)

### 8.1 ADR (numéro · date · décision en une ligne · statut)

| ADR | Date | Décision | Statut |
| --- | --- | --- | --- |
| 0001 | 2026-07-02 | LLM + STT servis par llama.cpp (pas vLLM) | accepté |
| 0002 | 2026-07-02 | Chatterbox Multilingual = provider TTS par défaut (licence MIT) | accepté |
| 0003 | 2026-07-02 | Admin des voix hors frontend OpenWebUI (zéro fork) | remplacé par 0009 |
| 0004 | 2026-07-02 | Qwen3.6-35B-A3B MoE, experts déchargés en RAM | accepté |
| 0005 | 2026-07-02 | Graphiti + Neo4j pour la mémoire en graphe bi-temporelle | accepté |
| 0006 | 2026-07-02 | Ingestion documentaire par polling mtime (inotify cassé en WSL) | accepté |
| 0007 | 2026-07-02 | Souveraineté plutôt qu'isolement réseau | accepté |
| 0008 | 2026-07-02 | Pont hôte = un seul pied hors Docker, sans intelligence, liste blanche | accepté |
| 0009 | 2026-07-07 | Sortie big bang d'OpenWebUI, architecture modulaire (4 responsabilités) | accepté, remplace 0003 |
| 0010 | 2026-07-07 | UI coquille : console + pastille, audio par la webview, modules web | accepté, précise 0009 |
| 0011 | 2026-07-08 | Politique de mémoire : l'utilisateur seul fait foi, capture à la clôture | accepté, précise 0005/0009 |
| 0012 | 2026-07-08 | Transport voix : cycle conversation, interruption, contrat DF, bouton d'abord | accepté, précise 0009/0010 |
| 0013 | 2026-07-19 | action-forge : agir par le code (CodeAct) en Atelier jetable, 3 paliers | accepté (non commité) |

Source : `docs/adr/*.md` (en-têtes).

### 8.2 Grillings datés cités dans les docs

- 2026-07-02 — grillings fondateurs (choix modèles/stack). Source : ADR 0001-0008.
- 2026-07-07 — forme UI, chemin audio, place du Rust → ADR 0010 ; roadmap.
- 2026-07-08 — politique de mémoire (après le faux fait) → ADR 0011 ;
  bornes de conversation → ADR 0012.
- 2026-07-10 — cadrage de la carte « redémarrage clean » (override wayfinder
  « plan, don't do »). Source : carte.md.
- 2026-07-18 — grilling du contrat action-forge (18 mentions) et du ticket 0029
  (correction ciblée des extractions). Source : ADR 0013, carte-action-forge,
  handoff 0018.
- 2026-07-19 — rédaction ADR 0013 ; cadrage CERP → carte-cerp. Source : carte-cerp.

### 8.3 Verdicts de tickets wayfinder (clos = validé)

- 22 tickets clos, 18 ouverts (au moment de l'observation). Cartes : `carte.md`
  (destination « la stack qui parle »), `carte-graphe-memoire.md`,
  `carte-action-forge.md`, `carte-cerp.md`. Source : frontmatter `statut:` de
  `docs/wayfinder/tickets/*.md`.
- Verdicts saillants (formulés en une ligne dans carte.md) :
  - 0003 : « la stack **parle** au poste Windows » (bouton → STT FR → DF → TTS).
  - 0006 : « **OUI**, l'obsolescence Graphiti tient en réel » (invalidation
    transitive, expérience « déménagement » Lyon→Paris).
  - 0012 : « la prémisse était fausse » (Chatterbox+torch 2.8 déjà en place),
    clone français validé à l'oreille, 1,75 s.
  - 0010 : « hey Jarvis » (canari anglais WASM) ouvre une conversation depuis la
    veille, détection 0.96.
  - 0031 : contrat action-forge tranché au grilling → ADR 0013 ; port 8500
    pressenti réfuté à l'audit des prémisses (occupé par le Pont hôte) → 8800.
- Un ticket ouvert reste le pivot de la carte principale : **0011 — recette
  finale ACCEPTANCE v2** (multi-tours, fin par silence, interruption, latence
  voix→voix ≤ 2 s à mesurer). Source : carte.md §Pas encore spécifié ; ticket 0011.

---

## 9. Interprétation (hypothèses) — à falsifier en phase Reconstruct

> Section explicitement spéculative. Aucune de ces lignes n'est un fait ; elles
> agrègent des observations ci-dessus en hypothèses sur le mode de décision de
> l'auteur, pour que la phase Reconstruct (ticket 0038) les mette à l'épreuve.

- **H-1 (confiance moyenne).** L'auteur privilégie la **réversibilité et
  l'isolement du risque** : ports/adaptateurs (O-2.1), extras optionnels
  (O-3.4), un seul pied hors Docker (O-2.8), sandbox jetable (ADR 0013),
  adaptateur réel « jamais exécuté » jusqu'à preuve (O-6.3). Falsifiable : un
  choix documenté où l'irréversibilité a été acceptée sans garde-fou.
- **H-2 (confiance élevée).** La décision passe par un **rite verbal (grilling)
  distinct de l'exécution** : décider, écrire l'ADR/le ticket, seulement
  ensuite coder — le commit ne porte pas la délibération (O-4.1, O-4.6, O-6.5).
  Falsifiable : des décisions structurantes prises directement dans le code
  sans trace ADR/ticket.
- **H-3 (confiance élevée).** L'auteur traite ses **propres croyances comme
  suspectes** : registre d'impasses péremptoires (O-4.3), audit des prémisses
  (O-4.8), « validé au réel » à l'oreille (O-4.7), diagnostic par la mesure
  (O-5.3). Le savoir non re-vérifié n'a pas de valeur. Falsifiable : décisions
  reposant sur un handoff cru sans re-vérification.
- **H-4 (confiance moyenne).** La **contrainte matérielle unique (16 Go / WSL /
  sm_120)** est le premier moteur de la majorité des choix techniques (llama.cpp
  vs vLLM, MoE offload, polling vs inotify, audio hors WSL, GPU hors Atelier) —
  davantage que des préférences de framework. Falsifiable : un choix majeur
  indépendant du budget VRAM/WSL.
- **H-5 (confiance moyenne).** L'auteur accepte des **big bangs assumés**
  (interruption de service sans limite, ADR 0009) quand le coût de maintenance
  d'un compromis (fork, monolithe) dépasse le coût de la reconstruction.
  Falsifiable : un cas où un compromis de maintenance a été préféré à une
  refonte propre.
- **H-6 (confiance faible).** La **langue française intégrale** et le
  vocabulaire de domaine tenu par glossaire ne sont pas cosmétiques mais un
  outil de pensée : nommer précisément (et renommer quand le sens bouge, O-3.6)
  fait partie de la décision. Falsifiable : dérives de nommage tolérées, ou
  anglicismes non justifiés dans le code métier.

---

## Annexe — méthode et limites de cette observation

- Sources primaires lues intégralement : les 13 ADR, CONTEXT.md, CLAUDE.md,
  docs/impasses.md, les 4 cartes wayfinder, README wayfinder, handoff 0018 +
  README handoffs, roadmap.md, personas/assistant.md, `git log` complet (57
  commits, messages + stats + dates), `git status` / `git diff --stat`.
- Sources échantillonnées (non exhaustives) : le code des forges via les
  ports/adaptateurs représentatifs (`dialogue-forge/app/{main,llm}`), les noms
  de toutes les fonctions de test, les pyproject/config. Les vues web vendorées
  (three.js, onnxruntime, `coquille/…`) et les binaires modèles n'ont pas été
  lus ligne à ligne (hors périmètre d'évidence décisionnelle).
- Limite assumée : les handoffs et cartes sont déjà des **condensés
  interprétés** de l'auteur ; ils sont ici traités comme évidence de premier
  ordre (ce sont ses mots) mais la circularité est à surveiller en phase
  Reconstruct (note de la carte-cerp).
- Ce document n'émet aucune recommandation, aucun plan, aucune reconstruction
  du CIR : il observe (périmètre du ticket 0036).
