---
label: cerp:compile-audit
ticket: 0040-cerp-audit-des-skills
cree: 2026-07-19
depend-de: [cir.md, test-en-aveugle.md]
---

# CERP — Audit des skills contre le CIR validé (ticket 0040, première marche de la phase Compile)

> **Nature.** Chaque skill de `~/.claude/skills` (45 SKILL.md), les automatismes
> du CLAUDE.md et la mémoire agent sont confrontés au CIR validé
> (`cir.md`, révisé post-aveugle 2026-07-19). Pour chacun : ce qu'il **sert**
> du CIR, où il le **contredit**, ce qu'il **rate**, ce qu'il **surspécifie**.
> **Rien n'est compilé ici** : l'audit fait graduer le brouillard
> « compilation » de la carte en tickets — la §9 les liste, ils se
> spécifieront au prochain grilling.
>
> **Verdicts** (traçables au CIR, référence entre parenthèses à chaque fois) :
> - **conforme** — porte fidèlement un ou plusieurs éléments du CIR ; aucune
>   action de compilation.
> - **à améliorer** — sert le CIR mais le contredit ou le rate en partie ;
>   candidat à un ticket de compilation.
> - **injustifié** — aucune évidence récurrente du corpus ne le justifie
>   (E6 : couche dormante) ou il appartient à un autre contexte de
>   l'utilisateur. **Injustifié ≠ à supprimer** : les skills sont globaux et
>   servent d'autres vies ; le verdict signifie seulement « aucune
>   compilation ne s'appuiera dessus » — et, pour quatre d'entre eux, « mine
>   connue s'ils sont invoqués dans ce dépôt ».
> - **manquant** — heuristique du CIR qu'aucun skill ne porte (§8 : ce
>   verdict est porté par le CIR, pas par un skill existant).
>
> Corpus relu pour cet audit : les 45 SKILL.md (intégralement), CLAUDE.md,
> les 6 fichiers de `~/.claude/projects/.../memory/`, `cir.md`,
> `test-en-aveugle.md`, `docs/wayfinder/carte-cerp.md`.

---

## 1. La couche sur mesure francophone — les compilés de fait

Ces quatre skills sont déjà des compilations du CIR avant la lettre (Q7 : rédigés
par l'agent sur demande, après grilling — donc validés par l'auteur, ce qui est
exactement ce que le CIR prédit qu'il validera).

### premisses — ~~à améliorer~~ **conforme** (retouche E3 appliquée le 2026-07-19, voir §10)

- **Sert** : I1 face (a) au mot près — « la faiblesse d'un agent n'est pas le
  code : ce sont les croyances gelées » ; le tri coût-si-faux × facilité = M2 ;
  la relève des impasses périmées = I8 ; le refus de persister le positif =
  coût n° 1 (la croyance non prouvée est la chose la plus chère).
- **Contredit / rate** : E3 — la lettre (« rien n'est persisté ») est pliée en
  pratique : le handoff 0018 persiste « Prémisses vérifiées cette session »,
  étiquetées périssables, et l'esprit est tenu (Q2 tranchée). Le skill dit déjà
  que les `différées` partent dans le handoff, mais pas que des *vérifiées*
  peuvent y voyager si elles sont étiquetées périssables.
- **Action candidate** : acter l'exception E3 dans le skill (une ligne), pour
  que la lettre rejoigne l'esprit au lieu de se faire plier à chaque session.

### impasses — **conforme**

- **Sert** : I8 champ à champ — trois champs, « Valide tant que », péremption
  décidable jamais par âge, périmer-pas-supprimer, frontière explicite
  impasse-conditionnelle vs contrainte-permanente (→ ADR/CLAUDE.md), consulter
  avant tout diagnostic (M2). La capture « à chaud » est tenue au grain du jour
  (Q3) — nuance de pratique, pas de texte. Rien à toucher.

### newbie — **conforme**

- **Sert** : I1 appliqué aux commandes — « aucun champ ne s'écrit sans source »,
  « le format ne crée pas la connaissance, il blanchit l'ignorance en
  structure » est du I1 pur (une croyance non vérifiée n'a pas de valeur, et un
  bloc faux-mais-confiant coûte plus qu'un doute visible) ; « la méthode est
  ici, les faits sont au projet » = I5 (la topologie vit dans CLAUDE.md, pas
  dans le skill). Signe de succès obligatoire = validation au réel (M8) portée
  jusque dans le terminal de l'utilisateur.

### delegate — **conforme**

- **Sert** : I4 et le coût n° 7 exactement — décision chère (le choix du
  modèle, le diagnostic d'un rouge structurel restent à l'agent principal),
  exécution bon marché à sous-traiter ; « le rapport du subagent est une
  déclaration, pas une preuve » = I1 ; vérification par le diff, pas par le
  compte rendu = la discipline anti-circularité du CIR lui-même ; interdictions
  systématiques (jamais commit, jamais gros téléchargement) = I4 + coût n° 5 ;
  brief audité par `/premisses` avant de figer = M2. La grille
  haiku→sonnet→opus avec escalade sur échec sert QD-2 (maximiser l'AFK à
  moindre coût). Rien à toucher.

---

## 2. Les adoptés à trace d'usage

### grilling (+ grill-me, grill-with-docs) — **conformes**

- **Sert** : I4 en méta-invariant d'entrée, confirmé le plus nettement au test
  en aveugle (constat G : le rite *est* la réponse spontanée du sujet). « Les
  faits dans le code, les décisions à l'utilisateur », une question à la fois,
  recommandation attachée, « do not enact until I confirm » : c'est M0 + M3.
  `grill-me` et `grill-with-docs` sont des alias fins (le second branche
  `/domain-modeling`, donc I7) — conformes par transitivité.

### domain-modeling — **conforme**

- **Sert** : I7 (glossaire canonique, challenger tout terme en conflit,
  CONTEXT.md « un glossaire, rien d'autre », mise à jour inline à chaque
  résolution) et le triple critère ADR de I8/M6 (difficile-à-inverser ∧
  surprenant ∧ vrai arbitrage — mot pour mot). La pratique le suit (CONTEXT.md
  réécrit aux ADR 0009/0011/0013, renommages tracés).

### tdd — **conforme**

- **Sert** : le corollaire de I2 (déterministe = testable, ce qui rend le TDD
  possible), M7 ; seams pré-validés avec l'utilisateur = I4 ; « red before
  green », tranches verticales. Lit CONTEXT.md et respecte les ADR (I7, I8).
- **Rate (mineur, sans action)** : il renvoie le refactoring au skill
  `code-review`, dormant ici (E6) — pointeur mort dans ce corpus, inoffensif.

### handoff — ~~à améliorer~~ **écart assumé, sans retouche** (grilling du 2026-07-19, voir §10)

- **Sert** : I8 registre périssable (compacter la session, ne pas dupliquer ce
  que portent ADR/tickets, référencer par chemin).
- **Contredit** : E5/Q4 — le skill sauve dans le **tmp de l'OS** ; la pratique
  versionne dans `docs/handoffs/` (18 handoffs, « seul le plus récent fait
  foi »). La convention du dépôt l'emporte à chaque session, mais c'est l'agent
  qui doit la ré-imposer contre le texte du skill.
- **Action candidate** : une ligne — « suivre la convention du dépôt si elle
  existe (répertoire de handoffs versionné), sinon le tmp de l'OS ».

### wayfinder — ~~à améliorer~~ **conforme** (M4 réfuté au grilling du 2026-07-19, voir §10)

- **Sert** : I4 (décisions-pas-livrables, HITL/AFK par type de ticket, « never
  resolve more than one ticket per session ») ; le fog of war est du I1
  appliqué à la planification (ne pas charter ce qui ne se constate pas
  encore) ; I8 (la carte est un index, la décision vit dans son ticket).
- **Rate** : le skill s'appuie sur le tracker configuré par
  `/setup-matt-pocock-skills` — **jamais exécuté ici** (E6). La convention
  réelle du dépôt (tracker wayfinder-local souverain, O-4.5/I6 :
  `docs/wayfinder/`, cartes multiples, tickets en fichiers, frontmatter
  `statut`/`bloque-par`/`carte`, labels `wayfinder:grilling|task|…`) n'est
  **écrite nulle part** — elle vit dans la pratique et se redécouvre par
  imitation des fichiers existants. C'est une étiquette de statut au sens du
  constat transversal §7 du CIR : ça marche tant que ça se rattrape.
- **Action candidate** : documenter la convention wayfinder-local (dans les
  Notes des cartes, un `docs/wayfinder/README` ou le CLAUDE.md — au grilling
  de trancher).

### prototype — **conforme**

- **Sert** : I3 au mot près — « throwaway from day one », marqué jetable, zéro
  persistance, « delete or absorb when done » ; et le coût §5 (jeter du code
  est bon marché, la seule chose qui vaut d'être gardée est la *réponse*,
  capturée au registre au bon niveau = I8).

### research — **conforme**

- **Sert** : I1 (sources primaires uniquement, chaque affirmation tracée à la
  source qui la possède) ; livrable = fichier Markdown à la convention du
  dépôt (I8). Pas de trace d'usage ici, mais rien à contredire — l'esprit
  « source primaire » est exactement celui du CIR (§Sources primaires
  re-consultées).

---

## 3. Dormants compatibles — candidats à adoption

### diagnosing-bugs — ~~à améliorer~~ **conforme dans ce dépôt** (adopté tel quel au grilling du 2026-07-19, voir §10)

- **Sert** : I1 diagnostic pur — la boucle de feedback rouge-capable avant
  toute hypothèse (« no red-capable command, no Phase 2 »), « measure first,
  fix second » pour la perf = exactement « par la mesure, jamais par
  l'impression » (O-5.3, le 0,9 tok/s au `curl` chronométré) ; hypothèses
  falsifiables avec prédiction = la discipline même du CIR ; débug
  maillon par maillon (chaîne voix du 2026-07-16) est ce skill en pratique,
  sans l'avoir invoqué (E6 : aucune trace).
- **Rate** : il ne consulte **pas le registre d'impasses** avant de
  diagnostiquer, alors que CLAUDE.md l'exige (« consulter ce registre avant
  tout diagnostic ») et que I8/M2 en font une étape du modèle. Un agent qui
  suit ce skill à la lettre re-paie des mines déjà payées.
- **Nuance** : sa Phase 5 impose d'écrire le test de régression avant le fix ;
  I1 prédit l'inverse pour un bug **non reproduit** (pas de test de régression
  sans repro) — compatible en fait, puisque la Phase 1 exige la repro d'abord,
  mais la préséance du registre doit être dite.
- **Action candidate** : adoption avec branchement — une Phase 0 « lire
  `docs/impasses.md`, annoncer les mines » (ou laisser `/impasses` l'imposer
  et référencer les deux dans CLAUDE.md).

### codebase-design — **conforme** (vocabulaire, dormant)

- **Sert** : le vocabulaire de I3 — ports/adaptateurs du dépôt parlent
  seam/adapter/deep module ; « one adapter = hypothetical seam, two = real »
  est satisfait partout (factice + réel = deux adaptateurs par port). Aucune
  contradiction ; utile comme référence si un grilling d'architecture le
  convoque. Aucune action.

### writing-great-skills — **conforme** (méta, servira la phase Compile)

- **Sert** : « a skill exists to wrangle determinism out of a stochastic
  system » est I2 appliqué à l'agent lui-même ; la chasse aux no-ops et à la
  surspécification est le critère « aucun artefact non justifié par de
  l'évidence récurrente » de la carte CERP. **C'est le standard de qualité que
  les tickets de compilation devront appliquer** quand ils retoucheront ou
  créeront des skills.

### wizard — **injustifié** (dormant, sans contradiction)

- Procédures manuelles guidées par bash — pourrait un jour servir les
  procédures multi-fenêtres Windows/WSL, mais `/newbie` couvre déjà ce besoin
  à la façon de l'auteur (blocs sourcés, pas de script qui s'exécute chez
  lui). I1 : ne rien bâtir tant qu'un besoin ne se constate pas.

---

## 4. Dormants injustifiés — l'écosystème que ce dépôt n'a pas

Tous présupposent le montage `setup-matt-pocock-skills` (tracker GitHub/local
`.scratch/`, labels de triage) qui n'a **jamais été exécuté** ici : le dépôt a
choisi le tracker wayfinder-local souverain (I6, O-4.5) et zéro issue GitHub
(E6). Verdict commun : **injustifié** — aucune compilation ne s'appuie dessus.
Particularités notables :

| Skill | Trace CIR | Note |
|---|---|---|
| ask-matt | E6 | Routeur vers des flows (`/to-spec` → `/implement` → commit) que le dépôt ne pratique pas ; son rôle d'index est tenu ici par CLAUDE.md + les cartes wayfinder. |
| code-review | E6 | Contenu (deux axes, smells Fowler) sain mais tourné vers un tracker absent. Si un besoin de revue se constate (I1), l'adapter sera un choix de compilation — pas avant. |
| to-prd / to-spec | E6 | Publient vers le tracker absent ; le rôle « figer la délibération » est tenu par ADR + tickets wayfinder (I4, I8). |
| to-issues / to-tickets | E6 | Idem ; le découpage en tranches est fait par les cartes wayfinder. |
| triage | E6 | Présuppose des rapports entrants qui n'existent pas (projet solo). |
| qa | E6 | `gh issue create` — tracker absent. |
| improve-codebase-architecture | E6, I6 | Rapport HTML via **CDN Tailwind/Mermaid** — requêtes sortantes non anonymisées vers des CDN, à rebours du réflexe souverain (mineur, mais réel). |
| design-an-interface | E6 | « Design it twice » — sain, aucun besoin constaté ; les grillings d'interface se font en I4 classique. |
| request-refactor-plan | E6 | GitHub issue en sortie — tracker absent. |
| ubiquitous-language | I7 ⚠ | **Contradiction potentielle** : écrit un `UBIQUITOUS_LANGUAGE.md` concurrent de CONTEXT.md, alors que I7 exige **un** glossaire canonique qui « fait foi ». S'il était invoqué ici, il créerait le doublon que I7 interdit. Ne jamais l'invoquer dans ce dépôt ; `domain-modeling` fait le même travail au bon endroit. |
| git-guardrails-claude-code | I1, I2 | Séduisant au regard de I2 (un garde déterministe plutôt qu'une discipline probabiliste) — mais I1 tranche : aucun `git push`/`reset` accidentel ne s'est **constaté** dans ce corpus, donc pas de garde-fou. À re-juger si un incident survient. |
| find-skills / setup-matt-pocock-skills | E6 | Méta-outillage d'installation ; `npx skills` = téléchargements (coût n° 5) et écosystème tiers — rien dans le CIR ne le convoque. |

### Mines connues — dormants qui commitent

Quatre skills contiennent une instruction `git commit` en contradiction
frontale avec « jamais de `git commit` » (I4, CLAUDE.md, mémoire) **s'ils sont
un jour invoqués dans ce dépôt** :

- **implement** — « Commit your work to the current branch » ;
- **setup-pre-commit** — commit final de smoke test (+ écosystème npm/Husky
  étranger aux forges Python/uv) ;
- **resolving-merge-conflicts** — « Stage everything and commit » ;
- **scaffold-exercises** — « then commit with `git commit` » (outillage de
  cours ai-hero, autre contexte).

Verdict : **injustifiés** ici, et la contradiction est une mine documentée —
pas un garde-fou à bâtir (I1 : aucune invocation accidentelle constatée), mais
un fait que le prochain réalignement CLAUDE.md peut choisir de consigner.

---

## 5. Hors corpus — les autres vies de l'utilisateur

`obsidian-vault` (vault D:), `teach`, `edit-article`, `writing-beats`,
`writing-fragments`, `writing-shape`, `loop-me`, `migrate-to-shoehorn`
(TypeScript), `claude-handoff` (variante de handoff lançant un agent de fond).
Verdict commun : **injustifié au regard de ce CIR** — aucun élément du CIR ne
les convoque, aucune contradiction active (sauf l'héritage `handoff` du tmp
pour `claude-handoff`, même remarque que §2). Aucune action ; ils ne
regardent pas ce dépôt. (Rappel de portée du CIR : « il ne généralise pas hors
corpus » — l'audit non plus.)

---

## 6. CLAUDE.md — la compilation de fait, presque à jour

Le CLAUDE.md du dépôt est déjà la principale compilation du CIR :

- **Sert** : I4 (« Analyser → proposer → attendre validation → coder en TDD »,
  jamais de commit, `/delegate` avec vérification finale) ; I1
  (`/premisses` obligatoire, « les croyances des handoffs se vérifient, ne se
  croient pas », adaptateurs « jamais exécuté à ce jour ») ; I8 (`/impasses` à
  chaud, consulter avant diagnostic, handoffs dernier-fait-foi) ; I5 (toute la
  §Plateforme : topologie sourcée, sm_120 « aucun binaire ne se présume
  compatible avant un test réel ») ; I7 (« tout est en français », CONTEXT.md
  fait foi) ; I3 (conventions ports/adaptateurs, factice par défaut) ; coût
  n° 5 (connexion lente, téléchargements par l'utilisateur).
- **Rate** :
  - **M8 n'est pas énoncé comme règle** : « valider au réel avant de clore,
    à l'oreille / au `curl` chronométré ; étiqueter “jamais exécuté” ce qui
    n'a pas tourné » se lit en creux dans §État particulier mais n'est pas une
    consigne de méthode — c'est pourtant l'invariant le plus falsifié (I1).
  - **Les seuils M4-M5 n'existent nulle part** : second LLM ? (non par défaut,
    I2) ; garde-fou ? (non tant que non constaté, I1) ; dépendance/serving ?
    (d'abord zéro re-build CUDA — coût n° 4, appris au test en aveugle S3 —
    puis licence permissive I6, source vérifiée par API, budget VRAM I5) ;
    big bang vs progressif ? (abandon → big bang, conservation → progressif,
    I3 reformulé S6).
  - **§État particulier est une étiquette à péremption rapide** (constat
    transversal §7) : la liste « adaptateurs réels jamais exécutés » y dérive
    dès qu'un adaptateur tourne (E2 l'a montré pour Graphiti). Aucun mécanisme
    de réconciliation n'existe.
- **Verdict : à améliorer** — c'est le réceptacle naturel d'une partie de la
  compilation (M8 en règle, seuils M4-M5, mines §4).

---

## 7. La mémoire agent — le registre qui dérive (E1 confirmé et étendu)

| Fichier (mtime) | Verdict | Trace |
|---|---|---|
| `workflow-voice-assistant.md` (07-02) | **à améliorer — périmé** | E1/Q8 : « zéro fork OpenWebUI » et le clone lecture seule `/home/ftk/openwebui/` sont morts depuis l'ADR 0009 (07-07) ; le reste (validation avant code, TDD, français, dernier handoff) reste vrai (I4, I7, I8). |
| `MEMORY.md` (index) | **à améliorer** | Répercute « zéro fork OpenWebUI » dans sa ligne d'index — même péremption. |
| `preference-conteneurisation-maximale.md` (07-08) | **à améliorer — partiellement périmé** | Nouvelle instance du constat §7, non relevée par le CIR : « candidats connus à conteneuriser : dialogue-forge (seule forge encore en `uv run`) » — or dialogue-forge tourne en Docker (CLAUDE.md : stack Docker = STT 8002, TTS 8100, **DF 8600** ; ports compose). La préférence elle-même (E4) reste vraie. |
| `telechargements-manuels-par-utilisateur.md` (07-10) | **conforme** | Coût n° 5, I6 ; mis à jour au fil des retours (assouplissement ≤ 3 Go tracé) — le contre-exemple qui prouve que la mémoire *sait* se mettre à jour quand un retour la frappe (E1 : elle n'est juste jamais réconciliée aux ADR). |
| `pas-de-co-authored-by.md` (07-03) | **conforme** | Convention de commit (I4 : le commit enregistre, il n'attribue pas) ; prime sur le défaut du harnais. |
| `format-texte-de-commit.md` (07-06) | **conforme** | Convention née d'un échec constaté (I1 : le garde-fou est venu *après* le problème, jamais avant — la mémoire est I1-conforme dans sa genèse). |

**Verdict d'ensemble : à améliorer** — E1 est la seule dérive que la méthode ne
rattrape pas seule, parce qu'aucun rite ne relit la mémoire aux ADR. C'est le
premier candidat de compilation (voir §8-M1).

---

## 8. Manquants — les heuristiques du CIR qu'aucun artefact ne porte

- **M1 — La réconciliation des étiquettes de statut** (constat transversal §7,
  E1, E2, §6 et §7 ci-dessus). L'ingénieur dont la méthode entière vise les
  croyances gelées n'a **aucun mécanisme** qui réconcilie périodiquement :
  mémoire agent ↔ ADR ; docstrings « jamais exécuté » ↔ premiers runs réels ;
  §État particulier du CLAUDE.md ↔ l'état réel. `/premisses` re-vérifie *en
  entrée de tâche* ce que la tâche touche — rien ne balaie le reste. C'est le
  manquant au plus fort rendement : trois instances confirmées (E1-E3) + une
  quatrième trouvée par cet audit (conteneurisation).
- **M2 — « Validé au réel » comme règle de clôture** (I1, M8) : à l'oreille
  pour l'audio, `curl` chronométré pour la latence, « ne clore qu'après »,
  étiqueter ce qui n'a pas tourné. Vécu partout (O-4.7), écrit nulle part
  comme consigne.
- **M3 — Les seuils de bascule M4-M5 du modèle de décision** : second LLM
  (I2), garde-fou (I1), tri des dépendances (CUDA → licence → source API →
  VRAM ; coût n° 4, I6, I5), big bang vs progressif (I3-S6). Chaque skill
  porte une étape du rite (M0 grilling, M2 premisses, M6 registres, M7 tdd,
  M9 handoff) ; **personne ne porte les seuils** — or c'est là que le test en
  aveugle a corrigé le CIR deux fois (S3, S6), donc là que le savoir est le
  plus neuf et le plus périssable.
- ~~**M4 — La convention wayfinder-local** (§2-wayfinder) : cartes, tickets,
  frontmatter, labels — pratiquée sur ~40 tickets, documentée nulle part.~~
  **RÉFUTÉ (2026-07-19, §10)** : la convention est intégralement documentée
  dans `docs/wayfinder/README.md` — que l'observation O-4.5 citait
  correctement ; c'est cet audit qui a perdu le fait en route (croyance
  fausse dans le document même qui traque les croyances gelées).
- **M5 — (mineur) L'exception E3 de premisses et la localisation des handoffs
  (E5)** : deux retouches d'une ligne chacune, listées en §1 et §2.

---

## 9. Synthèse

### Récapitulatif des 45 skills

| Verdict | Skills |
|---|---|
| **conforme** (12) | impasses, newbie, delegate, grilling, grill-me, grill-with-docs, domain-modeling, tdd, prototype, research, codebase-design, writing-great-skills |
| **à améliorer** (4) | premisses (E3), handoff (E5), wayfinder (M4), diagnosing-bugs (registre d'impasses) |
| **injustifié** (29) | ask-matt, code-review, to-prd, to-spec, to-issues, to-tickets, triage, qa, improve-codebase-architecture, design-an-interface, request-refactor-plan, ubiquitous-language ⚠, git-guardrails-claude-code, find-skills, setup-matt-pocock-skills, wizard, implement ⚠, setup-pre-commit ⚠, resolving-merge-conflicts ⚠, scaffold-exercises ⚠, obsidian-vault, teach, edit-article, writing-beats, writing-fragments, writing-shape, loop-me, migrate-to-shoehorn, claude-handoff |

(⚠ = contradiction active s'ils étaient invoqués ici : doublon de glossaire
pour ubiquitous-language ; `git commit` pour les quatre autres.)

Hors skills : **CLAUDE.md à améliorer** (§6), **mémoire agent à améliorer**
(§7, 3 fichiers sur 6).

### Ce que l'audit fait graduer (candidats tickets de compilation — à spécifier au grilling, rien n'est créé ici)

1. **Réconcilier la mémoire agent aux ADR** (M1, E1 + trouvaille
   conteneurisation) — la retouche immédiate *et* la décision de fond : un
   rite de réconciliation existe-t-il, et à quelle cadence ? (I1 dira : à un
   déclencheur constatable — p. ex. à chaque ADR nouveau — pas à l'âge.)
2. **Écrire M8 et les seuils M4-M5 dans le CLAUDE.md** (M2, M3) — la règle
   « validé au réel », les seuils second-LLM / garde-fou / dépendances /
   big-bang. Le savoir le plus fraîchement corrigé (S3, S6) est celui qui
   n'est écrit nulle part.
3. **Retouches d'une ligne** : premisses (exception E3), handoff (convention
   du dépôt d'abord, E5).
4. **Documenter la convention wayfinder-local** (M4).
5. **Adopter diagnosing-bugs avec branchement impasses** (§3) — ou décider que
   CLAUDE.md suffit.
6. **Consigner les mines** (§4 : quatre skills qui commitent,
   ubiquitous-language qui dédouble le glossaire) — une ligne au bon registre
   (CLAUDE.md ou impasses, au grilling de trancher : la contradiction est
   permanente tant que ces skills existent, ce qui plaide CLAUDE.md par la
   frontière de I8).

Aucun skill **nouveau** n'est justifié par de l'évidence récurrente au-delà de
ces six chantiers — le CIR se compile presque entièrement en *retouches* et en
*réalignement CLAUDE.md/mémoire*, pas en artefacts neufs. C'est cohérent avec
le CIR lui-même : la couche sur mesure existante est déjà sa compilation (Q7),
et I1 interdit d'en fabriquer davantage sans constat.

---

## 10. Addendum — verdicts du grilling de compilation (2026-07-19)

Les six chantiers du §9 ont été grillés et tranchés ; les verdicts amendés
ci-dessus (barrés) tracent ici :

- **M4 réfuté.** La convention wayfinder-local est intégralement portée par
  `docs/wayfinder/README.md` (cartes multiples, frontmatter, frontière,
  résolution, ticket unique) — O-4.5 la citait, l'audit l'a perdue. wayfinder
  repasse **conforme**. Le seul manquant résiduel : le CLAUDE.md ne pointe
  pas vers `docs/wayfinder/` — absorbé par le ticket 0042.
- **diagnosing-bugs adopté tel quel, zéro retouche.** Le CLAUDE.md impose
  déjà « consulter le registre avant tout diagnostic » à toute session, skill
  invoqué ou non ; la Phase 0 serait un garde-fou pour un problème jamais
  constaté (I1). À re-juger si une session au skill invoqué saute le registre.
- **premisses : retouche E3 appliquée** (une ligne dans le SKILL.md local :
  les *vérifiées* peuvent voyager dans le handoff si étiquetées périssables —
  seul persistage admis). La lettre rejoint l'esprit ; **conforme**.
- **handoff : pas de retouche.** Skill partagé (symlink, autres vies) et le
  CLAUDE.md porte déjà la convention `docs/handoffs/` — 18 handoffs prouvent
  qu'elle tient. E5 requalifié **écart assumé**.
- **Règle générale dégagée** : *les skills locaux se compilent, les skills
  partagés se surchargent par le CLAUDE.md.*
- **Chantiers → tickets** : 2 tickets au lieu de six —
  0041 (réconciliation mémoire : balayage-par-ADR + règle du premier run,
  chantier 1) et 0042 (réalignement CLAUDE.md : M8, seuils M4-M5, mines,
  pointeur wayfinder — chantiers 2, 4-résiduel et 6). Les chantiers 3 et 5
  sont clos par le présent addendum.

Bilan amendé : **15 conformes** (+wayfinder, +diagnosing-bugs, +premisses),
**1 écart assumé** (handoff), **29 injustifiés** (inchangé), **manquants
restants M1-M3** (M4 réfuté, M5 clos).
