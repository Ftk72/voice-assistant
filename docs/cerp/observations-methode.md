# CERP — Observe (méta) : ce que l'utilisateur *déclare* de sa méthode

> Ticket wayfinder 0037, phase « Observe » du protocole CERP (Observe → Reconstruct →
> Validate → Compile → Predict). Ce document observe la **couche déclarée** de la méthode :
> les *skills* de l'agent (`~/.claude/skills/`), la *mémoire agent* du projet
> (`~/.claude/projects/-home-ftk-voice-assistant/memory/`) et les **sections méthode**
> du `CLAUDE.md` du dépôt. Il ne dit rien de la pratique réelle — c'est l'objet du
> ticket 0036 (observation du dépôt). Les deux rapports seront confrontés plus tard.

## Vigilance circularité (cadre non négociable, grilling du 2026-07-19)

Tout ce qui suit est une **déclaration**, pas une preuve de pratique. Trois précautions
tenues bout à bout :

1. Skills et mémoire sont déjà des **condensés interprétés**. On les consigne comme
   « le skill X impose… », « la mémoire retient que… », jamais comme « l'utilisateur
   fait… ».
2. **Origine des artefacts** — signalée systématiquement :
   - Les six fichiers de mémoire portent tous `metadata: node_type: memory, type:
     feedback, originSessionId: …` : ce sont des entrées **écrites par l'agent** à partir
     de retours utilisateur en cours de session, pas de la main de l'utilisateur. La
     mémoire est donc le *récit que l'agent fait* des exigences utilisateur — doublement
     interprété.
   - Quatre skills sont des **répertoires locaux** propres à cette installation
     (`delegate`, `impasses`, `newbie`, `premisses`) : français, vocabulaire du projet,
     manifestement **sur mesure**. Reste à établir (question ouverte) s'ils sont écrits de
     la main de l'utilisateur ou rédigés/raffinés par un agent — leur prose est très
     travaillée, façon essai de méthode.
   - Tous les autres skills sont des **liens symboliques** vers
     `/mnt/c/Users/ftk/.agents/skills/` : un jeu partagé, en anglais, orienté tracker
     GitHub et « Matt Pocock » (`/setup-matt-pocock-skills`). Ce sont des skills
     **importés/génériques** ; leur simple présence ne prouve aucun usage sur ce projet.
3. Chaque déclaration ci-dessous est **sourcée** (fichier + ligne). Les interprétations
   sont isolées dans des sous-sections « Interprétation (hypothèse) ». Les tensions
   entre déclaré et pratiqué sont formulées en **questions ouvertes**, à trancher contre
   le rapport du dépôt — pas en conclusions.

---

## 1. Skills sur mesure (répertoires locaux, français, propres au projet)

### 1.1 `delegate` — déléguer puis vérifier
Fichiers : `~/.claude/skills/delegate/SKILL.md`, `.../delegate/BRIEF.md`.

**Impose :**
- Choisir soi-même le modèle du subagent selon une grille `haiku` / `sonnet` / `opus`,
  **annoncer** le choix en une ligne et continuer **sans attendre validation**
  (SKILL.md:23-33). En cas de doute, prendre **le plus léger** (SKILL.md:34-35).
- Construire le brief à partir **du `CLAUDE.md` du dépôt courant**, en y recopiant les
  règles pertinentes — « le subagent ne devine rien » (SKILL.md:39-43).
- **Auditer les prémisses du brief (`/premisses`) avant de le figer** (SKILL.md:45-48).
- Lancer le subagent avec `run_in_background: false` (SKILL.md:50-51).
- **Vérifier soi-même** ce qui a été touché : relancer tests + lint des composants
  modifiés, valider la config d'orchestration touchée, relire les fichiers critiques,
  confronter le rapport au diff (SKILL.md:55-66). « Le rapport du subagent est une
  déclaration, pas une preuve » (SKILL.md:57).
- Rapport final avec **sorties réelles**, « pas “ça passe” » (SKILL.md:76-77).

**Interdit :**
- Déléguer si ≤ 3 fichiers localisés, si correction d'un rouge déjà diagnostiqué, ou si
  la tâche dépend du contexte frais de conversation (SKILL.md:13-17).
- Mettre dans le brief autre chose que ce dont le subagent a besoin ; systématiquement
  interdire au subagent `git commit`, gros téléchargements, et hors-périmètre
  (SKILL.md:51-53).
- Relancer un subagent **neuf** après un échec structurel : renvoyer le diagnostic au
  **même** via `SendMessage`, contexte intact (SKILL.md:68-72).

**Ritualise :** chemins absolus partout ; « un exemple vaut dix règles » (pointer un
fichier à imiter) ; un brief par subagent pour les lots parallèles sans fichier partagé
(BRIEF.md:38-46). Gabarit de brief à sections obligatoires : Conventions / Tâche / Hors
périmètre / Interdictions / Validation attendue / Rendu attendu (BRIEF.md:8-36).

### 1.2 `impasses` — registre du savoir négatif tactique
Fichier : `~/.claude/skills/impasses/SKILL.md`.

**Impose :**
- **Capturer au moment de l'échec**, pas en fin de session (SKILL.md:3, 8).
- Écrire dans `docs/impasses.md` (le créer au premier usage) une entrée à **trois
  champs** : *Tenté* / *Pourquoi c'est mort* / *Valide tant que* (SKILL.md:8-15).
- Le champ **« Valide tant que »** est décisif : il rend la péremption *décidable* (par
  version ou par état), **jamais par âge** (SKILL.md:17).
- **Consulter le registre avant tout diagnostic ou exploration** et annoncer les mines
  connues de la zone (SKILL.md:3, 19).

**Interdit :** supprimer une impasse dont la condition est tombée — on la **périme**, elle
redevient une prémisse à re-vérifier (SKILL.md:21).

**Ritualise :** frontière avec les ADR — une contrainte **permanente** (sans condition de
validité formulable) va en ADR ou CLAUDE.md, pas dans le registre (SKILL.md:23).

### 1.3 `newbie` — format de toute commande destinée à l'utilisateur
Fichier : `~/.claude/skills/newbie/SKILL.md`.

**Impose :**
- Le déclencheur : dès qu'une commande **sort de ton terminal et entre dans le sien**
  (SKILL.md:10). L'unité est la **fenêtre**, pas la commande (SKILL.md:8).
- **Sourcer chaque champ** avant de l'écrire (doc projet, config lue, ou commande qu'on
  vient de lancer) ; « le format ne crée pas la connaissance, il blanchit l'ignorance en
  structure » (SKILL.md:12-14). Si l'on ne peut pas sourcer, **on ne produit pas le
  bloc** (SKILL.md:16).
- Un bloc **autonome et rejouable** : état → chemin absolu (`cd`) → commandes, une seule
  zone copiable par fenêtre (SKILL.md:20-32).
- Déclarer, **hors** de la zone copiable : l'environnement, le **sort de la fenêtre**
  (bloque/à garder ouverte vs libérable), et un **signe de succès en une ligne**
  observable (SKILL.md:34-38).
- « La méthode est ici, les faits sont au projet » : le CLAUDE.md déclare environnements
  et topologie ; s'il ne déclare rien, **la première livraison est cette déclaration**,
  pas une commande (SKILL.md:18).

**Interdit :** aucune exception pour les commandes « évidentes » — « l'évidence est un
jugement, et c'est ton jugement qui échoue » (SKILL.md:10). Laisser dans la zone copiable
la moindre chose « à composer par lui » (SKILL.md:22, 44).

**Ritualise :** « Fini quand » — chaque champ a une source nommable, chaque fenêtre
déclare son sort et son signe de succès (SKILL.md:42-44).

### 1.4 `premisses` — audit des croyances avant toute tâche significative
Fichier : `~/.claude/skills/premisses/SKILL.md`.

**Impose :**
- Trois mouvements avant la tâche : **Extraire** les prémisses invisibles (« ce fichier
  existe », « le handoff est encore vrai », « ce schéma/API a cette forme ») — les
  croyances héritées d'un handoff sont **suspectes d'office** (SKILL.md:8) ; **Trier** par
  coût-si-faux × facilité de vérification (SKILL.md:9) ; **Vérifier ou déclarer** à bas
  coût (`ls`, `grep`, `--dry-run`, requête API légère), sans téléchargement lourd
  (SKILL.md:10).
- Chaque prémisse reçoit un statut : `vérifié ✓` / `réfuté ✗` / `assumé ~` / `différé ⏳`
  (ce dernier **nomme son échéance**) (SKILL.md:11-13).
- Avant l'audit, **lire `docs/impasses.md`** : toute impasse dont la condition est tombée
  redevient une prémisse à retester (SKILL.md:15).

**Interdit :** **persister** la sortie — « le positif vérifié se re-vérifie la prochaine
fois ; le persister fabriquerait les croyances gelées de la prochaine session »
(SKILL.md:17). La sortie est éphémère et n'est « pas du code, pas un plan » (SKILL.md:19).

**Ritualise :** aiguillage des sorties — une prémisse réfutée coûteuse → `/impasses` ;
une croyance structurante actée → CLAUDE.md ou ADR ; les `différées` → checklist finale
que le handoff emporte (SKILL.md:17).

### Interprétation (hypothèse) — les quatre skills sur mesure
Ces quatre skills forment un **cycle épistémique** auto-référent : `premisses` alimente
`impasses` (savoir négatif), `impasses` réalimente `premisses` (péremption), `newbie`
exige que tout fait soit sourcé au projet, `delegate` invoque `premisses` avant de figer
un brief. Hypothèse : l'utilisateur (ou l'agent qui a rédigé ces skills) **traite la
croyance non vérifiée comme le risque numéro un** de l'agent — thème répété mot pour mot
(« croyances gelées », « le rapport est une déclaration, pas une preuve », « sourcer avant
d'écrire »). À confirmer : est-ce une posture *déclarée* seulement, ou observable dans le
dépôt ? → questions ouvertes §5.

---

## 2. Skills importés mais adoptés (référencés par le CLAUDE.md / la pratique du dépôt)

Ces skills sont des liens symboliques (jeu générique), mais le `CLAUDE.md` ou l'arborescence
du dépôt les **désignent explicitement** — ils sont donc *adoptés*, pas seulement présents.

### 2.1 `grilling` (+ on-ramps `grill-me`, `grill-with-docs`)
Fichiers : `.../grilling/SKILL.md`, `.../grill-me/SKILL.md`, `.../grill-with-docs/SKILL.md`.

**Impose :** interviewer l'utilisateur **relentlessly**, une question à la fois, en
attendant la réponse avant de continuer (SKILL.md:6-8) ; proposer une réponse recommandée
par question (SKILL.md:6) ; chercher les **faits** dans le code, mais laisser les
**décisions** à l'utilisateur (SKILL.md:10). **Interdit :** exécuter le plan avant
confirmation d'une compréhension partagée (SKILL.md:12) ; poser plusieurs questions à la
fois (SKILL.md:8). `grill-with-docs` couple le grilling à `/domain-modeling`
(grill-with-docs/SKILL.md:7). *Note d'origine : anglais, générique ; adopté car le
CLAUDE.md et la mémoire le nomment (`/grilling`).*

### 2.2 `wayfinder`
Fichier : `.../wayfinder/SKILL.md`. *Note d'origine : générique, orienté « issue tracker »,
mais **manifestement en usage** (le dépôt a un `docs/wayfinder/` complet, et le présent
ticket 0037 en découle).*

**Impose :** planifier une masse de travail trop grande pour une session comme une **carte
partagée** de tickets d'investigation (SKILL.md:7) ; **nommer la destination** en premier,
elle fixe le périmètre (SKILL.md:9, 111) ; désigner par **nom**, jamais par id nu
(SKILL.md:16-17) ; **planifier, ne pas faire** par défaut — produire des décisions, pas des
livrables, sauf override dans les *Notes* de la carte (SKILL.md:11-13) ; **claim** d'un
ticket par assignation avant tout travail (SKILL.md:67, 122). **Interdit :** résoudre
**plus d'un ticket par session** (SKILL.md:105). **Ritualise :** distinction *fog of war* /
ticket / hors-périmètre (SKILL.md:82-101) ; quatre types de tickets research / prototype /
grilling / task, HITL vs AFK (SKILL.md:73-80).

### 2.3 `tdd`
Fichier : `.../tdd/SKILL.md`. *Note d'origine : générique/anglais ; adopté (le CLAUDE.md
impose le TDD et la mémoire nomme `/tdd`).*

**Impose :** la boucle **red → green** (SKILL.md:34) ; tester au **seam** (interface
publique), et **seulement à des seams pré-convenus avec l'utilisateur** (SKILL.md:18-24) ;
lire `CONTEXT.md` pour que noms de tests et vocabulaire épousent le domaine (SKILL.md:10) ;
travailler en **tranches verticales** (un test → une implémentation), en *tracer bullets*
(SKILL.md:30). **Interdit :** trois anti-patterns — tests couplés à l'implémentation,
**tautologiques**, et **horizontal slicing** (tous les tests puis toute l'implémentation)
(SKILL.md:26-30) ; le refactoring **n'est pas** dans la boucle (SKILL.md:36).

### 2.4 `domain-modeling` (+ `ubiquitous-language`)
Fichiers : `.../domain-modeling/SKILL.md`, `.../ubiquitous-language/SKILL.md`. *Adopté : la
mémoire nomme `/domain-modeling` pour CONTEXT.md/ADR.*

**Impose :** construire/affûter activement le modèle de domaine (SKILL.md:8) ; challenger
un terme qui entre en conflit avec `CONTEXT.md` (SKILL.md:46) ; mettre à jour `CONTEXT.md`
**inline**, sans batcher (SKILL.md:60-62). **Interdit :** traiter `CONTEXT.md` comme une
spec, un brouillon ou un dépôt de décisions d'implémentation — « c'est un glossaire, rien
d'autre » (SKILL.md:64) ; proposer un ADR sauf si les **trois** critères sont réunis
(difficile à inverser, surprenant, vrai arbitrage) (SKILL.md:66-73).

### 2.5 `handoff` / `claude-handoff`
Fichiers : `.../handoff/SKILL.md`, `.../claude-handoff/SKILL.md`. *Note d'origine : le skill
générique `handoff` **sauve dans le dossier temporaire de l'OS** (handoff/SKILL.md:8), ce
qui **contredit** la pratique du dépôt (handoffs versionnés dans `docs/handoffs/`). Le
CLAUDE.md du dépôt définit son propre rituel `/handoff` (CLAUDE.md:19-20). Voir tension
§5.* **Impose (skill générique) :** résumer la conversation pour un agent frais, inclure une
section « suggested skills », ne pas dupliquer ce qui vit déjà en spec/ADR/issue (les
référencer), caviarder les secrets (handoff/SKILL.md:8-16).

---

## 3. Skills importés/génériques présents mais non rattachés au projet (inventaire)

Présents (liens symboliques vers le jeu partagé), **aucune trace de rattachement** au
CLAUDE.md ou à la mémoire du projet — leur présence ne prouve aucun usage ici. Recensés
pour complétude, sans détail de méthode :

- **Flux « engineering » Matt Pocock** : `code-review` (revue à deux axes Standards/Spec en
  sous-agents parallèles + baseline de *code smells* Fowler), `diagnosing-bugs` (boucle de
  diagnostic en 6 phases, « build a feedback loop » d'abord), `codebase-design` /
  `design-an-interface` / `improve-codebase-architecture` (vocabulaire des *deep modules*),
  `to-issues` / `to-tickets` / `to-spec` / `to-prd` / `triage` / `qa` / `implement` /
  `request-refactor-plan` (chaîne spec→tickets→triage→implémentation sur tracker GitHub),
  `setup-matt-pocock-skills`, `ask-matt` (routeur de skills), `prototype`, `research`,
  `resolving-merge-conflicts`. Tous supposent un *issue tracker* et le vocabulaire
  Matt Pocock — orientation qui **n'est pas** celle déclarée du dépôt (français, tracker
  local wayfinder).
- **Outillage divers non lié au domaine** : `git-guardrails-claude-code`, `setup-pre-commit`
  (Husky/lint-staged, écosystème JS), `migrate-to-shoehorn` (TypeScript), `scaffold-exercises`
  (cours), `obsidian-vault` (chemin `/mnt/d/Obsidian Vault/…`, hors dépôt), `wizard`
  (bash wizard), `find-skills`, `loop-me`, `teach`.
- **Skills d'écriture** : `edit-article`, `writing-beats`, `writing-fragments`,
  `writing-shape`, `writing-great-skills` (référence pour rédiger des skills). Hors domaine
  logiciel du projet.

### Interprétation (hypothèse) — deux régimes de skills
Hypothèse : l'utilisateur superpose **deux couches** de méthode déclarée : (a) une couche
générique importée (Matt Pocock + outils JS/écriture), largement dormante sur ce projet ;
(b) une couche **sur mesure francophone** (les 4 skills locaux + wayfinder/grilling/tdd
adoptés) qui est celle réellement invoquée par le CLAUDE.md et la mémoire. À vérifier
contre le dépôt : lesquels de ces skills laissent une trace d'usage réelle ? → §5.

---

## 4. Mémoire agent — ce qu'elle *retient* et *corrige*

Six fichiers ; tous marqués `type: feedback` (donc **écrits par l'agent** d'après un retour
utilisateur — cf. §Vigilance). Chaque entrée : le **fait retenu** → le **comportement
corrigé**.

- **`MEMORY.md`** (index, lignes 3-7) — pointe vers les cinq entrées ci-dessous.
- **`workflow-voice-assistant.md`** — *Retient :* commencer chaque session par le **dernier
  handoff** (numéro le plus élevé), seul lui fait foi (l.12) ; par étape **analyser →
  proposer → expliquer → attendre validation → coder en TDD → tests → doc**, jamais coder
  sans validation (l.13) ; **zéro fork/modification d'OpenWebUI** (l.14) ; répondre **en
  français** (l.15). *Corrige :* l'agent qui coderait sans valider, redériverait le contexte
  au lieu de lire le handoff, ou forkerait OpenWebUI. *Note :* mention « zéro fork
  OpenWebUI » et clone `/home/ftk/openwebui/` (l.14) **périmée** par l'ADR 0009 (sortie
  d'OpenWebUI) — la mémoire n'a pas suivi.
- **`pas-de-co-authored-by.md`** — *Retient :* jamais de ligne « Co-Authored-By: Claude » ni
  aucune signature d'agent dans les messages de commit (l.10). *Corrige :* l'ajout
  automatique d'un trailer d'attribution ; demande explicite du 2026-07-03, messages
  « propres à copier-coller » (l.12-14).
- **`telechargements-manuels-par-utilisateur.md`** — *Retient :* les gros téléchargements
  (> 100 Mo, modèles) sont faits **manuellement par l'utilisateur** ; ne jamais lancer
  `hf download`, `docker pull/build` lourd, `uv sync` avec torch sans accord **au moment
  même** — un « fais toutes les étapes » ne couvre pas les téléchargements (l.10-14).
  *Corrige :* deux refus concrets du 2026-07-05 (~3 Go STT Voxtral) ; ne pas exécuter les
  scripts de download « pour tester » (`bash -n` seulement). *Assouplissement du
  2026-07-10 :* subagents autorisés à ≤ 3 Go dans le cadre des tickets wayfinder (l.16).
- **`format-texte-de-commit.md`** — *Retient :* « donne-moi le texte du commit » = fournir
  une **commande git exécutable** (`git add` si nouveaux fichiers + `git commit` enveloppant,
  heredoc pour le multi-lignes), jamais le message nu (l.10, 14-16). *Corrige :* incident du
  2026-07-06 — message nu collé dans bash, chaque ligne interprétée comme commande
  (« Stack: command not found ») (l.12).
- **`preference-conteneurisation-maximale.md`** — *Retient :* archi **modulaire, un maximum
  de services conteneurisés** ; si conteneurisable, alors **doit** l'être — préférer un
  service compose versionné à un réglage hôte caché (l.10-13). *Corrige :* proposer d'emblée
  la voie conteneurisée face à un problème d'infra (l.19-21). *Exception :* host-bridge, hors
  Docker par nécessité (ADR 0008) (l.16-17).

### Interprétation (hypothèse) — ce que la mémoire priorise
Cinq des six entrées touchent au **contrôle que l'utilisateur garde sur les actes
irréversibles ou coûteux** : commits (2 entrées), téléchargements (1), validation avant code
(1), et souveraineté/reproductibilité de l'infra (1). Hypothèse : la mémoire encode surtout
des **garde-fous contre l'autonomie de l'agent sur ce qui engage** (le réseau, l'historique
git, le disque, l'architecture), plus qu'une méthode de conception. À confronter au dépôt.

---

## 5. Sections « méthode » du CLAUDE.md (déclaration faîtière du dépôt)

Fichier : `/home/ftk/voice-assistant/CLAUDE.md`.

**Impose :**
- Cycle **Analyser → proposer → attendre validation → coder en TDD → tests → doc**
  (l.24) ; **jamais de `git commit`**, l'utilisateur commite (l.25) ; aucun téléchargement
  lourd (> 100 Mo) sans accord, **lancé par l'utilisateur** (l.26-29).
- Déléguer les grosses implémentations via `/delegate` (haiku→sonnet→opus), vérification
  finale par l'agent principal (l.30-31) ; auditer les prémisses via `/premisses` avant
  toute tâche significative — « les croyances des handoffs se vérifient, ne se croient
  pas » (l.32-33) ; capturer toute piste morte à chaud dans `docs/impasses.md`
  (`/impasses`) et **consulter ce registre avant tout diagnostic** (l.34-35) ; toute
  commande destinée à l'utilisateur suit `/newbie` (l.36-40).
- **Lire avant de coder** : `CONTEXT.md` (glossaire fait foi), `docs/adr/`, dernier
  handoff (l.11-20). Conventions forges : Python 3.12/uv, `uv run pytest` + `ruff check`
  verts, ports/adaptateurs (port ABC + adaptateur factice + adaptateur réel « jamais
  exécuté à ce jour »), modèle à imiter `memory-forge/` (l.41-62).

### Interprétation (hypothèse) — le CLAUDE.md orchestre les skills sur mesure
Le CLAUDE.md **câble** les quatre skills locaux (`/delegate`, `/premisses`, `/impasses`,
`/newbie`) dans un ordre rituel, et adopte `/tdd`, `/grilling`, `/domain-modeling`,
`/handoff`. Hypothèse : la méthode *déclarée* du projet **n'est pas** dans un skill isolé
mais dans ce montage CLAUDE.md + skills sur mesure + mémoire. Les skills importés génériques
sont largement hors de ce montage.

---

## 6. Tensions pressenties entre déclaré et pratiqué — QUESTIONS OUVERTES

À trancher contre le rapport du dépôt (ticket 0036), **pas** des conclusions.

1. **Validation avant code.** Le déclaré est strict (« jamais coder sans validation »,
   workflow-voice-assistant.md:13 ; CLAUDE.md:24). *Le dépôt montre-t-il des tranches
   codées puis validées en bloc, ou toujours une validation en amont ?* La mémoire admet
   déjà une souplesse (« validation en bloc “enchaîne les N étapes” acceptée »,
   workflow-voice-assistant.md:13) — jusqu'où va-t-elle réellement ?

2. **`premisses` « éphémère, jamais persisté » (premisses/SKILL.md:17-19) vs traces
   documentaires.** L'audit des prémisses est censé ne rien laisser. *Trouve-t-on malgré
   tout des audits de prémisses figés dans des handoffs/docs du dépôt ? Si oui, la règle
   d'éphémérité est-elle tenue ou contournée ?*

3. **`impasses` « capturer à chaud, au moment de l'échec » (impasses/SKILL.md:3,8).** *Les
   entrées de `docs/impasses.md` datent-elles de l'instant de l'échec, ou sont-elles
   ajoutées en fin de session (donc reconstruites) ?* Observable via l'historique git du
   fichier — objet du ticket 0036.

4. **Handoff : deux localisations contradictoires.** Le skill générique `handoff` sauve
   **dans le dossier temporaire de l'OS** (handoff/SKILL.md:8) ; le dépôt versionne ses
   handoffs dans `docs/handoffs/` (CLAUDE.md:19-20, workflow-voice-assistant.md:12). *Quelle
   règle la pratique suit-elle réellement, et le skill importé a-t-il jamais été utilisé tel
   quel ?*

5. **Couche générique dormante.** ~30 skills importés (flux Matt Pocock, outils JS,
   écriture) ne sont rattachés ni au CLAUDE.md ni à la mémoire. *Le dépôt porte-t-il la
   moindre trace d'usage de `code-review`, `to-issues`, `triage`, `diagnosing-bugs`, etc.,
   ou la pratique n'invoque-t-elle que la couche sur mesure ?* (Le tracker déclaré est
   wayfinder-local, pas GitHub — ce que ces skills présupposent.)

6. **Conteneurisation maximale (preference-conteneurisation-maximale.md:10-13) vs réalité
   hybride.** Le déclaré veut tout en conteneur ; le CLAUDE.md lui-même liste des exceptions
   (transport-voix et coquille en **natif Windows**, host-bridge hors Docker). *L'écart
   déclaré/pratiqué est-il assumé (exceptions documentées) ou subi (dérive) ?* La mémoire
   nomme dialogue-forge et transport-voix comme « candidats à conteneuriser » restés en
   `uv run` (l.21) — dette déclarée, à vérifier.

7. **Origine des skills sur mesure.** *Les skills `delegate` / `impasses` / `newbie` /
   `premisses` sont-ils écrits de la main de l'utilisateur, ou rédigés par un agent ?* Leur
   prose très ciselée et méta est un indice, pas une preuve. La réponse change le statut de
   ce rapport : déclaration *de l'utilisateur* vs déclaration *d'un agent sur l'utilisateur*.

8. **Péremption non suivie dans la mémoire.** `workflow-voice-assistant.md:14` retient
   encore « zéro fork OpenWebUI » et le clone `/home/ftk/openwebui/`, alors que l'ADR 0009 a
   acté la sortie d'OpenWebUI. *La mémoire agent est-elle mise à jour au rythme des ADR, ou
   accumule-t-elle des croyances périmées ?* (Ironie à noter, non à conclure : le skill
   `premisses` cible précisément les « croyances gelées héritées ».)
