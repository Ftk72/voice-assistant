---
label: cerp:reconstruct+validate
ticket: 0038-cerp-reconstruire-le-cir
cree: 2026-07-19
depend-de: [observations-depot.md, observations-methode.md]
---

# CERP — CIR : modèle cognitif prédictif de l'ingénieur (tickets 0038, phases Reconstruct + Validate documentaire)

> **Nature.** Le CIR est le plus petit modèle cognitif **prédictif** de l'auteur
> du dépôt — pas une explication du dépôt. Objectif : prédire ses décisions sur
> un problème neuf. Il a été soumis au **test en aveugle** (ticket 0039,
> `test-en-aveugle.md` : score 3,5/6 dimensions testables) et **révisé en
> retouche ciblée le 2026-07-19** (clause big bang de I3, coût CUDA, Q1/Q7
> closes, I4 promu méta-invariant d'entrée) ; il sera compilé (0040) ; rien ne
> se compilera qui n'en dérive.
>
> **Discipline.** Chaque invariant porte cinq champs — *évidence pour*, *évidence
> contre*, *alternatives*, *confiance*, *pouvoir prédictif* — et une **trace**
> (O-x.y du rapport dépôt, source primaire lue, ou hash de commit). Chaque
> élément est trié **convention** (choix local) / **contrainte** (subie) /
> **préférence** (transportable ailleurs). Ce qui n'a pas survécu à la
> falsification est en §Rejets. On cherche l'explication **la plus simple** avant
> d'ajouter une heuristique : quand N patterns dérivent d'un principe, le CIR
> porte le principe.
>
> **Sources primaires re-consultées pour falsifier** (au-delà des deux rapports
> d'observation) : les 13 ADR, `docs/impasses.md` (+ son `git log --follow`),
> handoff 0018, CONTEXT.md, CLAUDE.md, `git log` complet (57 commits), les six
> fichiers de `~/.claude/projects/.../memory/` (+ mtimes), les quatre SKILL.md
> sur mesure.

---

## 0. La forme la plus courte du modèle

Trois principes portent l'essentiel. Tout le reste en dérive ou les nuance.

- **P1 — La réalité est la seule monnaie qui autorise une dépense.** L'auteur ne
  dépense ni *croyance* ni *construction* sur du non-prouvé. Une croyance non
  re-vérifiée ne vaut rien ; un garde-fou pour un problème non **constaté** ne se
  bâtit pas.
- **P2 — Un seul cerveau ; tout le reste bête, déterministe, testable.**
  L'intelligence (le LLM, la décision) se concentre en un lieu ; une seconde
  surface stochastique est un coût à fuir, payé en code déterministe.
- **P3 — Contenir le rayon de souffle plutôt qu'éviter le risque.** Le risque
  n'est pas évité, il est **isolé** pour rester jetable ou réversible à bas coût.

Ces trois-là prédisent, à eux seuls, la majorité des choix techniques observés.
Les invariants I1–I3 les portent ; I4–I8 ajoutent le rite de décision, les
axiomes subis, et la gestion du savoir.

---

## 1. Invariants d'ingénierie

### I1 — La réalité est la seule monnaie qui autorise une dépense (= P1)

Deux faces d'un même principe : (a) *épistémique* — une croyance non re-vérifiée
n'a pas de valeur ; (b) *YAGNI par le constat* — on ne construit rien contre un
problème seulement anticipé, on attend qu'il « se constate ».

- **Évidence pour.** Face (a) : audit des prémisses obligatoire, « les croyances
  des handoffs se vérifient, ne se croient pas » (CLAUDE.md ; O-4.8) ; sortie
  premisses **jamais persistée** pour ne pas « fabriquer des croyances gelées »
  (premisses/SKILL.md:17) ; « validé au réel » à l'oreille comme seul critère de
  clôture (O-4.7) ; diagnostic **par la mesure, jamais par l'impression** (O-5.3,
  impasses 2026-07-17 : 0,9 tok/s mesuré au `curl` chronométré) ; adaptateur réel
  étiqueté « jamais exécuté à ce jour » tant qu'il n'a pas tourné (O-6.3) ;
  handoff 0018 re-teste des docstrings et corrige « six → huit types » plutôt que
  de les croire (l.21, 57-59). Face (b) : ADR 0011 répète quatre fois le motif —
  « On ne bâtira une réécriture que si une perte réelle **se constate** »,
  « à n'activer que si un faux fait santé **se constate** », « Aucun garde-fou
  déterministe … tant que la coexistence de doublons **ne se constate pas** »,
  « slot à valeur unique … prématuré tant que le double n'est pas constaté » ;
  ADR 0013 diffère la micro-VM et le token d'API (« défense en profondeur jugée
  sans objet », « reportée au palier où le besoin la justifiera »).
- **Évidence contre.** Le mot d'éveil français est ajouté « dès la v1 » comme
  « chantier à risque » (ADR 0009 §Conséquences) — construction anticipée d'une
  capacité non encore constatée nécessaire. Mais c'est un **choix produit**
  (l'assistant vocal *doit* pouvoir s'éveiller), pas un garde-fou spéculatif : la
  face (b) parle des protections/complexités défensives, pas des capacités du
  produit. L'exception ne mord pas.
- **Alternatives.** « Il est simplement prudent/rigoureux » — trop faible : la
  prudence n'explique pas le *refus actif de persister* un audit positif ni le
  « tant que ça ne se constate pas » érigé en règle de conception. « C'est une
  discipline agent imposée, pas la sienne » — écartée : le motif traverse les
  ADR (ses mots, §Contexte/Décision), pas seulement les skills.
- **Confiance : très élevée.** C'est le principe le plus falsifié et le plus
  transversal.
- **Pouvoir prédictif.** Sur un problème neuf, prédit qu'il **refusera de coder
  la protection tant que le problème n'est pas observé** (il livrera le chemin
  nominal + un point d'audit, en différant le garde-fou), qu'il **exigera une
  mesure/un run réel avant de déclarer quoi que ce soit fonctionnel**, et qu'il
  **re-vérifiera toute croyance héritée** (handoff, docstring, ticket) plutôt que
  de s'y fier. Prédit aussi qu'il n'ajoutera pas de test de régression pour un
  bug non reproduit.
- **Tri : préférence** (épistémique, transportable à tout projet).

### I2 — Un seul cerveau ; tout le reste bête, déterministe, testable (= P2)

L'intelligence se concentre en un lieu unique (le LLM orchestré) ; chaque autre
composant **exécute sans décider**. Une seconde surface LLM/stochastique est
traitée comme un coût (latence + « nouvelle surface d'hallucination » + non
testable).

- **Évidence pour.** ADR 0011 dec. 2 & 4 : filtre backchannels et filtre de
  pertinence **déterministes**, « jamais un juge LLM » (O-6.6) ; ADR 0009 : le
  problème n'était pas la cascade mais « le monolithe qui l'orchestre » ; ADR
  0013 « **Un seul cerveau** : dialogue-forge transmet l'énoncé tel que dit et ne
  planifie rien » (alternative « deux cerveaux qui planifient » écartée) ;
  host-bridge « sans intelligence » (O-2.8), coquille « n'assemble » / jamais de
  logique métier (O-6.4), transport « aucune logique métier » (ADR 0009 §2).
  Corollaire : déterministe = testable, ce qui **rend possible** le TDD (O-3.2,
  O-4.1) — les deux principes se tiennent.
- **Évidence contre.** L'action-forge (ADR 0013) introduit une **seconde** boucle
  CodeAct pilotée par LLM, distincte de dialogue-forge. Mais l'ADR le cadre
  précisément comme *un seul cerveau par responsabilité* (« la décomposition en
  Actions appartient à l'action-forge », dialogue-forge « ne planifie rien ») :
  ce n'est pas deux cerveaux sur la même tâche, c'est un déplacement du cerveau,
  pas un doublement. Confirme plutôt qu'il ne réfute.
- **Alternatives.** « Simple séparation des responsabilités (SRP) » — trop
  générique : SRP n'implique pas le refus systématique du *second LLM* ni le
  choix du déterministe **contre** le pratique. La spécificité (fuir la surface
  stochastique) est le prédicteur, pas SRP.
- **Confiance : élevée.**
- **Pouvoir prédictif.** Face à un problème « et si on demandait au LLM de… »,
  prédit qu'il **cherchera d'abord une solution déclarative/déterministe** (table,
  ontologie, filtre) et n'acceptera un LLM que si le déterministe échoue
  *constaté* (cf. I1). Prédit qu'un nouveau composant naîtra « bête » (exécute,
  ne décide pas) et que la coquille/le transport ne gagneront jamais de logique
  métier.
- **Tri : préférence** d'architecture (transportable).

### I3 — Contenir le rayon de souffle plutôt qu'éviter le risque (= P3)

Le risque n'est pas fui ; il est **encapsulé** pour rester bon marché à jeter ou
à annuler. Le défaut est toujours l'option inerte/factice ; le risqué est isolé
derrière une frontière.

- **Évidence pour.** Port ABC + adaptateur **factice par défaut** + adaptateur
  réel séparé, sélection par Settings, import réel *à la demande* (O-2.1, O-2.2) ;
  dépendances lourdes en **extra optionnel** isolé, extras inconciliables
  déclarés conflictuels (O-3.4) ; **un seul pied hors Docker**, borné liste
  blanche argv (O-2.8, ADR 0008) ; **Atelier jetable** — conteneur détruit après
  compte rendu, « qu'on peut perdre sans regret », socket monté dans la forge
  seule, aucun montage sensible (ADR 0013) ; **sûreté par surface bornée** plutôt
  que par auth (ADR 0013 : « la garde est dans la surface de l'API »).
- **Évidence contre — décisive et retenue.** ADR 0009 : l'auteur choisit la
  sortie **big bang** d'OpenWebUI (« interruption de service assumée, sans limite
  de durée ») **contre** la recommandation explicite de l'agent
  d'« étranglement progressif, service jamais interrompu » — soit contre l'option
  la plus réversible. → I3 n'est **pas** « maximiser la réversibilité » (H-1
  d'origine, rejetée en §Rejets R1). Ce qui survit : il **contient** le risque
  (l'image OpenWebUI « reste sur disque comme filet d'urgence » ; l'Atelier est
  jetable), il ne cherche pas à éviter les gros gestes. **Le test en aveugle
  (S6) borne une seconde fois la clause** : devant « Pipecat 2.0 casse l'API »,
  il choisit la **migration par couche** — l'option que le CIR prédisait
  rejetée. Relecture : le big bang de l'ADR 0009 accompagnait un **abandon**
  (OpenWebUI supprimé de l'architecture) ; Pipecat, lui, **reste**. Ce qui
  survit : *big bang pour ce qu'il abandonne, progressif pour ce qu'il
  conserve* — l'interruption de service n'est bon marché que quand elle paie
  une simplification définitive, pas une montée de version.
- **Alternatives.** « Aversion au risque » — réfutée par le big bang. « Goût de
  la table rase » — réfutée par le filet d'urgence systématique. La synthèse
  *containment* explique les deux.
- **Confiance : élevée** sur le containment (défaut inerte, jetable) ;
  **moyenne** sur la clause big bang, falsifiée puis reformulée au test en
  aveugle (S6).
- **Pouvoir prédictif.** Prédit que tout nouveau composant à risque naîtra avec
  un **défaut inerte** (factice/no-op) et un adaptateur réel séparé « jamais
  exécuté » ; qu'un travail dangereux (exécution de code, action sur l'hôte) sera
  poussé dans une **enveloppe jetable/bornée** plutôt que sécurisé en place ;
  qu'il **acceptera un big bang** (interruption assumée, filet peu coûteux) pour
  un composant qu'il **abandonne**, mais choisira la **montée de version
  progressive** (couche de compatibilité) pour un composant qu'il **conserve**
  (test en aveugle S6).
- **Tri : préférence** d'architecture. (Le *pied hors Docker* est, lui, une
  **contrainte** — cf. I5/ADR 0008 ; l'instinct de le borner est la préférence.)

---

## 2. Le rite de décision

### I4 — Décider est un acte verbal (grilling) séparé de l'exécution ; l'humain tranche, l'agent exécute — **méta-invariant d'entrée**

La délibération vit dans un **rite parlé** (grilling) puis se fige dans un
ADR/ticket ; le code vient après ; le commit **enregistre**, il ne délibère pas.
Sur les décisions, l'humain garde la main ; l'exécution se délègue.
**Promu méta-invariant au test en aveugle (constat G)** : devant six scénarios
neufs, la réponse spontanée du sujet est le rite lui-même (« grilling →
trade-offs explicités → je tranche ») — le rite précède même le nommage et le
cadrage ; le contenu des décisions est **co-produit par la dyade**
utilisateur+agent, l'utilisateur en étant l'arbitre.

- **Évidence pour.** Cycle « Analyser → proposer → **attendre validation** →
  coder en TDD → tests → doc » (CLAUDE.md ; O-4.1) ; 41 fichiers de docs citent
  « grilling », mais **3 commits sur 57** seulement (O-4.6, O-6.5) → la
  délibération est dans l'ADR/ticket, le commit l'enregistre ; handoff 0018 : une
  **session entière de grilling, « aucune ligne de code écrite »** ; grilling/
  SKILL.md : « laisser les décisions à l'utilisateur, chercher les faits dans le
  code » ; delegate/SKILL.md : déléguer l'exécution puis **vérifier soi-même**
  (« le rapport du subagent est une déclaration, pas une preuve »).
- **Évidence contre — décisive.** ADR 0009 §Alternatives : l'agent recommandait
  l'étranglement progressif ; **c'est l'utilisateur qui a tranché** le big bang.
  Ceci ne réfute pas I4 : au contraire, il en est la preuve la plus nette — sur
  une décision structurante, l'agent propose, **l'humain décide**. Aucun cas
  trouvé de décision structurante prise directement dans le code sans trace
  ADR/ticket (H-2 non falsifiée).
- **Alternatives.** « C'est juste un workflow imposé par le CLAUDE.md » — mais le
  CLAUDE.md est **son** montage (§I7/observations-methode §5), et l'override du
  big bang montre qu'il *exerce* réellement la décision, il ne subit pas le
  process.
- **Confiance : très élevée** (relevée au test en aveugle : c'est l'invariant
  confirmé le plus nettement, énoncé spontanément par le sujet).
- **Pouvoir prédictif.** Prédit qu'aucun choix d'architecture ne sera codé sans
  passer par une proposition soumise à validation ; que la **volumétrie**
  (>3 fichiers ou lot conséquent) sera **déléguée** avec vérification finale par
  lui, mais que **la décision et le diagnostic d'un rouge** resteront à lui
  (delegate/SKILL.md:13-17) ; qu'un compte rendu d'agent sera confronté au diff,
  jamais cru sur parole.
- **Tri : préférence** (HITL sur la décision, délibération verbale) +
  **convention** (formats ADR/ticket/handoff).

---

## 3. Les axiomes subis et auto-imposés

### I5 — La contrainte matérielle est un axiome à tester empiriquement, pas une préférence

Le trio **16 Go VRAM partagés / WSL2 / Blackwell sm_120** est traité comme un
fait premier : « aucun binaire CUDA ne se présume compatible avant un test
réel ». Il **borne la couche service/infra**, non l'architecture.

- **Évidence pour.** ADR 0004 (MoE, experts déchargés en RAM ; budget VRAM
  chiffré par service), O-5.1 ; impasses matérielles denses et chiffrées :
  torch 2.6 sans sm_120 (2026-07-06), KV non borné → VRAM saturée (`-c 16384`),
  `-j 4` borné sinon OOM WSL, build lourd → LLM paginé ÷37, audio de conversation
  hors WSL (WebRTC), GPU hors Atelier (ADR 0013). CLAUDE.md §Matériel/Topologie.
- **Évidence contre — recadre H-4.** La majorité des choix **d'architecture et de
  produit** sont **indépendants** du matériel : Chatterbox choisi pour sa
  **licence MIT** (ADR 0002), Graphiti pour la **bi-temporalité** (ADR 0005),
  modularité/français/TDD/ports pour la **méthode** (ADR 0009). → l'affirmation
  « le matériel est le premier moteur de la *majorité* des choix » (H-4) est
  **rejetée** (R2) ; ce qui survit : le matériel gate la couche *serving/infra*.
- **Alternatives.** « Il aime optimiser la VRAM » — non : il la subit et la
  **mesure** ; l'optimisation est contrainte, pas plaisir (cf. le débit paginé
  traité comme une panne, pas comme un terrain de jeu).
- **Confiance : élevée** pour « contrainte qui gate le serving » ; le rejet de
  H-4-fort est ferme.
- **Pouvoir prédictif.** Prédit que tout choix de *serving/dépendance GPU* sera
  subordonné au budget VRAM et **validé par un run réel** avant d'être déclaré
  bon ; mais qu'un choix d'*architecture/produit* obéira, lui, aux préférences
  I1–I3 et aux valeurs I6, **pas** au matériel. Utile pour ne pas sur-prédire le
  matériel là où il ne joue pas.
- **Tri : contrainte** (subie) ; la **réponse** (tester au réel, chiffrer,
  borner) est une préférence — c'est I1 appliqué au matériel.

### I6 — Souveraineté et licence sont des axiomes non négociables (valeur auto-imposée)

Modèles et données personnelles en local ; requêtes sortantes **anonymes**
tolérées ; le cloud managé est refusé « jamais » ; la licence permissive oriente
les choix.

- **Évidence pour.** ADR 0007 (souveraineté redéfinie, pas isolement ; O-5.5) ;
  ADR 0002 (Chatterbox retenu **licence MIT**) ; ADR 0013 (« aucune sandbox
  managée cloud, **jamais** » ; E2B/Modal/Daytona écartés comme contraires à
  ADR 0007) ; tracker **wayfinder-local** plutôt que GitHub « souverain, comme le
  reste » (O-4.5) ; openWakeWord re-sourcé pour cause de licence NC incompatible
  Apache-2.0 (impasse 2026-07-17).
- **Évidence contre.** Aucune trouvée : même sous forte pression (agir par le
  code, où une sandbox cloud managée serait le chemin le plus court), le refus
  tient (ADR 0013). C'est la valeur la plus stable du corpus.
- **Alternatives.** « Contrainte de connexion lente » — insuffisant : la
  connexion lente explique le refus des *téléchargements*, pas le refus **de
  principe** du cloud même gratuit/rapide, ni le tri par licence.
- **Confiance : très élevée.**
- **Pouvoir prédictif.** Prédit qu'il **écartera d'emblée** toute solution SaaS/
  cloud/API tierce, même si elle est objectivement la plus simple, et qu'entre
  deux dépendances il **regardera la licence** (permissive gagnante) et
  **vérifiera la source par API** avant toute commande de téléchargement.
  **Nuance du test en aveugle (S3)** : la licence est un **véto**, pas le
  premier filtre — devant une dépendance de serving, le premier filtre est
  « la chaîne CUDA tient-elle sans re-build ? » (coût n° 4) ; la licence
  n'arrive qu'ensuite. Le véto lui-même reste sans contre-exemple.
- **Tri : préférence/valeur** auto-imposée (transportable ; il pourrait la
  relâcher ailleurs mais l'évidence dit qu'il ne la relâche pas).

---

## 4. La gestion du savoir et du langage

### I7 — Nommer précisément est un acte de conception ; le vocabulaire se maintient activement

Français intégral (code, tests, docs, commits) et **glossaire canonique**
(CONTEXT.md « fait foi ») **réécrit à chaque déplacement de sens**.

- **Évidence pour.** Tout le code en français, identifiants métier (`Orchestrateur`,
  `DeltaTexte`, `AppelOutil` ; O-3.1) ; tests en phrases-assertions (O-3.2) ;
  CONTEXT.md réécrit aux ADR 0009/0011/0013, renommages **tracés** (« Action » →
  « Commande du catalogue », ADR 0013 §Conséquences ; O-3.6) ; skill
  domain-modeling adopté (« challenger un terme en conflit avec CONTEXT.md »,
  « c'est un glossaire, rien d'autre »).
- **Évidence contre.** Anglicismes techniques tolérés où ils sont le nom propre
  de l'objet (`backchannel`, `CodeAct`, `fake`, `health`) — mais toujours pour un
  terme sans équivalent français consacré, jamais pour un concept métier. La
  discipline **métier** n'a pas de contre-exemple ; H-6 (dérives tolérées) non
  confirmée → la langue **n'est pas** cosmétique.
- **Alternatives.** « Simple préférence linguistique » — trop faible pour
  expliquer la **réécriture active** du glossaire à chaque ADR et le traçage des
  renommages. Le prédicteur est « nommer = concevoir », pas « écrire en
  français ».
- **Confiance : moyenne-élevée** (le *français* est solide ; « outil de pensée »
  reste partiellement interprétatif → à confirmer au test en aveugle).
- **Pouvoir prédictif.** Prédit que devant une ambiguïté de vocabulaire il
  **s'arrêtera pour renommer et mettre à jour CONTEXT.md** avant de coder, et
  qu'un concept métier neuf recevra un **nom français précis** (pas un terme
  fourre-tout — cf. `Sujet`/`Chose` écartés, ADR 0011 §Alternatives).
- **Tri : convention** (le français = choix local) + **préférence** (nommer comme
  acte de conception = transportable).

### I8 — Le savoir se structure en artefacts durables à péremption décidable, jamais par âge

Trois registres distincts par leur durée de vie : **ADR** (permanent : difficile
à inverser ∧ surprenant ∧ vrai arbitrage), **impasses** (conditionnel : champ
« Valide tant que » → péremption *décidable*, jamais par âge, marquée barrée
jamais supprimée), **handoffs** (périssable : seul le dernier fait foi).

- **Évidence pour.** O-4.2 (ADR remplacent/précisent explicitement), O-4.3
  (impasses à trois champs, péremption décidable ; impasses/SKILL.md:17 « jamais
  par âge »), O-4.4 (handoffs, dernier fait foi) ; frontière explicite ADR vs
  impasse (contrainte permanente → ADR/CLAUDE ; conditionnelle → registre —
  impasses/SKILL.md:23) ; git log : entrées d'impasse committées **le jour même
  (±1 j)** de la date d'échec qu'elles portent (`git log --follow` sur
  `impasses.md`) → capture au grain du jour.
- **Évidence contre.** Le `git log` montre des impasses committées **en lot**
  (fin de session), et une entrée datée 07-06 committée 07-07 : la capture « à
  chaud, au moment de l'échec » (impasses/SKILL.md:3) est tenue **au jour**, pas à
  la minute — le commit est batché. Nuance, pas réfutation.
- **Alternatives.** « Simple goût de la doc » — réfuté par la **typologie par
  durée de vie** (permanent/conditionnel/périssable) et le mécanisme de
  péremption : ce n'est pas documenter, c'est **dater la validité**.
- **Confiance : élevée.**
- **Pouvoir prédictif.** Prédit que face à un savoir neuf il choisira le registre
  par sa **durée de vie** : une contrainte permanente → ADR/CLAUDE ; un piège
  conditionnel → impasse avec « Valide tant que » ; un état de session →
  handoff. Prédit qu'il **ne supprimera jamais** une impasse (il la périme) et
  qu'il **ne créera un ADR** que si les trois critères sont réunis.
- **Tri : préférence** méthodologique (transportable) + **convention** (formats).

---

## 5. Fonction de coût cognitive

Ce qui est **cher** pour cet ingénieur (par ordre de coût décroissant, inféré) :

1. **La croyance non prouvée** (le plus cher). Il re-vérifie, mesure, refuse de
   persister un positif, étiquette « jamais exécuté ». (I1 ; O-4.8, O-5.3, O-6.3.)
2. **Une seconde surface stochastique / d'hallucination.** Il paie du code
   déterministe pour ne pas l'ouvrir. (I2 ; O-6.6, ADR 0011.)
3. **L'irréversibilité des *données/faits*, pas du service.** Asymétrie nette :
   un faux fait en mémoire force une **purge complète du graphe** (ADR 0011
   §Contexte) — coût maximal ; une **interruption de service** (big bang, ADR
   0009) est **bon marché** (assumée sans limite). Ce qu'il protège, c'est
   l'intégrité de la mémoire/vérité, pas la disponibilité.
4. **Refaire la chaîne CUDA/toolchain sm_120** (torch nightly, re-builds) :
   deal breaker avéré **avant même l'examen de licence** — face au STT
   « meilleur mais torch nightly », c'est le motif de refus qu'il nomme, pas la
   licence. (Test en aveugle S3 ; impasses torch/sm_120 de juillet.)
5. **La bande passante / le téléchargement lourd** (contrainte connexion lente) :
   >100 Mo = geste de l'utilisateur ; source vérifiée par API avant toute
   commande. (O-5.2 ; mémoire « téléchargements manuels ».)
6. **La VRAM (16 Go)** : ressource rare budgétée par service. (I5, ADR 0004.)
7. **Son attention de décideur** : précieuse (il reste HITL sur les décisions)
   mais son *temps d'exécution* est **délégable** (delegate). Asymétrie : décision
   chère, exécution bon marché à sous-traiter — sous réserve de vérification.
   Corollaire tranché au test en aveugle (QD-2) : la granularité de validation
   se règle pour **maximiser les tâches AFK**. (I4.)
8. **La souveraineté** : coût infini à violer (« jamais » de cloud). (I6.)

Ce qui est **bon marché** (et le prédit) : **jeter** du code/des conteneurs
(Atelier jetable, adaptateurs factices, big bang), **réécrire** le glossaire,
**interrompre** le service. Il dépense volontiers là où le geste est contenu et
récupérable ; il économise durement la croyance, la VRAM, la bande passante et
l'intégrité des données.

---

## 6. Première forme du modèle de décision d'ingénierie (livrable 3 — proposée, non définitive)

Comment il paraît passer d'un **problème neuf** à une **décision**. Forme
proposée ; la version définitive est au brouillard de la carte.

0. **Ouvrir le rite.** Tout problème neuf commence par un grilling — l'agent
   conseille, expose les trade-offs ; l'humain tranchera. (I4 en méta-invariant
   d'entrée ; test en aveugle, constat G : c'est la réponse spontanée aux six
   scénarios, avant tout contenu.)
1. **Nommer la destination et le vocabulaire.** Wayfinder : la destination fixe
   le périmètre ; challenger tout terme en conflit avec CONTEXT.md. *(Question :
   quel est le mot juste ? quelle est la fin visée ?)*
2. **Auditer les prémisses.** Extraire les croyances invisibles, lire
   `docs/impasses.md`, trier par coût-si-faux × facilité, vérifier à bas coût.
   *(Question : qu'est-ce que je crois ici sans preuve ? quelle mine connue ?)*
3. **Griller.** Interroger relentlessly, une question à la fois ; chercher les
   **faits** dans le code/la mesure, laisser la **décision** à l'humain.
4. **Chercher le plus simple / le plus déterministe.** *Seuils de bascule :*
   - un LLM de plus ? → **non par défaut** (I2), sauf déterministe constaté
     insuffisant ;
   - un garde-fou/une complexité défensive ? → **non tant que le problème ne se
     constate pas** (I1) ; livrer le chemin nominal + un point d'audit ;
   - une dépendance/un serving ? → **d'abord : aucun re-build de la chaîne
     CUDA/toolchain** (deal breaker, test en aveugle S3) ; puis licence
     permissive (I6, véto), source vérifiée par API, budget VRAM tenu (I5).
5. **Placer le risque, pas l'éviter.** Défaut inerte + adaptateur réel isolé ;
   travail dangereux en enveloppe jetable/bornée ; big bang **acceptable si**
   coût de maintien du compromis > coût de reconstruction **et** filet peu
   coûteux disponible. *(Seuil : existe-t-il un filet bon marché ?)*
6. **Acter au bon registre.** ADR **seulement si** difficile-à-inverser ∧
   surprenant ∧ vrai arbitrage ; sinon ticket ; piège conditionnel → impasse
   (« Valide tant que ») ; état → handoff.
7. **Coder en TDD** (factice d'abord), **déléguer si volumineux** (>3 fichiers)
   avec vérification finale par lui.
8. **Valider AU RÉEL** (à l'oreille pour l'audio, `curl` chronométré pour la
   latence) ; **ne clore qu'après**. Étiqueter « jamais exécuté » ce qui n'a pas
   tourné.
9. **Capturer le savoir négatif à chaud** (impasse) ; **handoff** en fin ; ne
   jamais commiter (l'utilisateur commite).

Boucle de rappel : les étapes 2, 8 et le §Écarts disent que ce cycle est une
**réconciliation périodique** avec la réalité, pas continue — d'où I1.

---

## 7. Écarts déclaré-vs-pratiqué (les trouvailles les plus précieuses)

**Constat transversal : les étiquettes de statut se périment plus vite qu'elles
ne se corrigent** — chez l'ingénieur dont la méthode entière vise justement les
croyances gelées. Sa méthode les **rattrape** quand il re-vérifie (elle marche),
mais **entre deux réconciliations, elles dérivent**. Trois instances confirmées :

- **E1 — Mémoire agent non réconciliée aux ADR (Q8 tranchée : oui).**
  `~/.claude/projects/.../memory/workflow-voice-assistant.md` (mtime **2026-07-02**,
  jamais retouché) tient encore « **zéro fork OpenWebUI** » et le clone
  `/home/ftk/openwebui/`, **périmés** par l'ADR 0009 (2026-07-07). Le fichier
  `telechargements-manuels…` a, lui, été mis à jour (mtime 07-10, assouplissement
  ≤3 Go) → la mémoire est mise à jour **au fil de nouveaux retours**, jamais
  **réconciliée aux ADR**. Ironie : le skill `premisses` cible précisément les
  « croyances gelées héritées ». *Trace : mtimes + contenu ; observations-methode
  §6 Q8.*
- **E2 — Étiquettes de code « jamais exécuté » périmées.** L'adaptateur Graphiti
  tourne au réel depuis les tickets 0016-0021, mais des docstrings « jamais
  exécuté » **traînent périmées** dans `graphiti.py` (handoff 0018 l.57-59 :
  « ne pas s'y fier, ne pas non plus les croire sur parole : re-tester »). Même
  classe que E1. *Trace : handoff 0018.*
- **E3 — `premisses` « jamais persisté » vs handoffs qui persistent une section
  « Prémisses vérifiées » (Q2 tranchée : plié, esprit tenu).** Le skill interdit
  de persister l'audit (premisses/SKILL.md:17) ; le handoff 0018 **persiste**
  pourtant « Prémisses vérifiées cette session ». La **lettre** est pliée, mais
  **l'esprit** est tenu : elles y sont explicitement étiquetées « à ne pas
  re-payer, mais **périssables** … vraies aujourd'hui, pas éternellement »
  (handoff 0018 l.19, 69). *Trace : handoff 0018 ; premisses/SKILL.md.*

Écarts **assumés** (documentés, non subis) — Q6, Q4, Q5 tranchées :

- **E4 — Conteneurisation maximale vs exceptions natives (Q6).** transport-voix,
  coquille (natif Windows) et host-bridge (hors Docker) sont des exceptions
  **de contrainte externe** (media WebRTC ne traverse pas WSL — impasse
  2026-07-08 ; Tauri natif ; ADR 0008), **documentées** dans le CLAUDE.md. Reste
  une **dette déclarée** (dialogue-forge/transport-voix « candidats à
  conteneuriser » restés en `uv run`, mémoire) — donc majorité assumée, petite
  dette reconnue. *Trace : CLAUDE.md ; mémoire ; impasse 2026-07-08.*
- **E5 — Handoff : deux localisations (Q4 tranchée).** Le skill générique
  `handoff` sauve dans le tmp de l'OS ; la pratique **versionne** dans
  `docs/handoffs/` (18 handoffs). La convention du dépôt **l'emporte** ; le
  comportement du skill importé n'est pas suivi. *Trace : O-4.4 ;
  observations-methode §2.5.*
- **E6 — Couche générique dormante (Q5 tranchée).** Aucune trace d'usage de
  `code-review`, `to-issues`, `triage`, `diagnosing-bugs` (tracker GitHub qu'ils
  présupposent = absent ; O-4.5) ; seule la couche **sur mesure francophone** +
  les adoptés (grilling/tdd/wayfinder/domain-modeling/handoff) laissent une
  trace. *Trace : git log (zéro issue) ; O-4.5, O-4.6.*

---

## 8. Rejets (invariants candidats tués par la falsification)

- **R1 — « L'auteur privilégie la réversibilité / évite l'irréversibilité »**
  (H-1 tel que formulé). **Tué par** ADR 0009 §Alternatives : il choisit le
  **big bang irréversible** contre l'étranglement progressif *réversible*
  recommandé par l'agent. Reformulé en **I3** (contenir le rayon de souffle) : ce
  qu'il protège n'est pas la réversibilité du geste mais son **coût de
  récupération** (filet d'urgence, jetable). L'irréversibilité qu'il craint est
  celle des **données** (purge du graphe, ADR 0011), pas du service.
- **R2 — « La contrainte matérielle est le premier moteur de la *majorité* des
  choix »** (H-4 fort). **Tué par** ADR 0002 (licence), 0005 (capacité), 0009
  (méthode/valeur) : trop de choix majeurs sont indépendants de la VRAM/WSL.
  Réduit à **I5** : le matériel gate la couche *serving/infra*, pas
  l'architecture.
- **R3 — « Le grilling absent des commits révèle une délibération cachée. »**
  Sur-interprétation d'un simple fait de *localisation* (la délibération est dans
  l'ADR/ticket, pas dans le commit). N'est pas un invariant prédictif propre :
  absorbé par **I4**. *Trace : O-6.5.*
- **R4 — « Il aime optimiser la VRAM. »** Réfuté : il la **subit et la mesure**
  comme une panne (débit paginé ÷37, impasse 2026-07-17), il ne l'optimise pas
  par goût. Le prédicteur est I1 (mesurer) + I5 (contrainte), pas un plaisir
  d'optimisation.

---

## 9. Bilan de falsification des questions ouvertes (rapport méthode §6)

| # | Question | Verdict | Appui |
| --- | --- | --- | --- |
| Q1 | Validation avant code : stricte ou souple ? | **Tranchée (mostly)** : HITL sur la **décision** tenu (ADR 0009 override, handoff 0018 = grilling sans code) ; la **granularité** des lots est un cadran réglé par l'utilisateur (mémoire : « validation en bloc acceptée », phase-par-phase pour memory-forge). **Bascule tranchée au test en aveugle (QD-2)** : la granularité se règle pour **maximiser les tâches AFK** — HITL concentré aux bornes (grilling avant, vérification après). | I4 ; mémoire workflow ; test-en-aveugle.md |
| Q2 | `premisses` éphémère vs traces persistées | **Tranchée** : lettre pliée (handoffs persistent), esprit tenu (étiquetées périssables). | E3 |
| Q3 | Impasses capturées à chaud ou en fin de session | **Tranchée (au grain du jour)** : entrées committées le jour même (±1 j) de la date d'échec ; commit batché → « à la minute » non prouvable. | I8 ; `git log --follow` |
| Q4 | Localisation des handoffs | **Tranchée** : convention dépôt (`docs/handoffs/`) l'emporte, skill importé non suivi. | E5 |
| Q5 | Couche générique dormante | **Tranchée** : aucune trace d'usage ; seule la couche sur mesure + adoptés opèrent. | E6 |
| Q6 | Conteneurisation vs exceptions natives | **Tranchée** : exceptions de contrainte externe assumées + petite dette déclarée. | E4 |
| Q7 | Origine des skills sur mesure (main de l'utilisateur ou agent) | **Tranchée au test en aveugle (QD-1)** : « l'agent a rédigé les textes à ma demande, après un grilling » — la prédiction (indice faible sur pièces : sessions agent des commits 7741a12/d02c03e du 07-03) est confirmée mot pour mot. | commits 07-03 ; handoffs 0005/0006 ; test-en-aveugle.md |
| Q8 | Mémoire mise à jour au rythme des ADR ? | **Tranchée : non** — accumule des croyances périmées (mtime 07-02 « zéro fork »). | E1 |

**Tranchées : 8 / 8** — Q7 et la marge de granularité de Q1 ont été closes par
le test en aveugle (ticket 0039, 2026-07-19).

---

## 10. Récapitulatif — invariants au plus fort pouvoir prédictif (≤ 10 lignes)

1. **I1** — Ne dépense ni croyance ni construction sur le non-prouvé : re-vérifie
   tout, ne bâtit un garde-fou que quand le problème « se constate ». *(le plus
   prédictif : gouverne debug, tests, garde-fous, statuts.)*
2. **I2** — Un seul cerveau ; tout le reste bête et déterministe ; refuse le
   second LLM.
3. **I3** — Contient le risque (défaut inerte, jetable, filet) plutôt que
   l'éviter ; **big bang pour ce qu'il abandonne, progressif pour ce qu'il
   conserve** (reformulé au test en aveugle, S6).
4. **I4** — Décision = rite verbal (grilling→ADR) séparé du code ; l'humain
   tranche, l'agent exécute puis se fait vérifier.
5. **I6** — Souveraineté/licence non négociables : écarte tout cloud « jamais »,
   trie par licence.
6. **Coût** — Cher : croyance non prouvée, seconde surface stochastique,
   intégrité des **données** ; bon marché : jeter du code, interrompre le service.
   **Asymétrie clé** : irréversibilité des données ≫ irréversibilité du service.

---

## Annexe — bilan de production

- **Invariants retenus : 8** (I1–I8), dont 3 principes-mères (P1–P3 = I1–I3).
- **Candidats rejetés : 4** (R1–R4), tous reformulés ou absorbés (aucun rejet
  sec sans destination).
- **Questions ouvertes : 8 / 8 tranchées** — Q7 et la marge de Q1 closes au
  test en aveugle (0039).
- **Écarts déclaré-vs-pratiqué confirmés : 6** (E1–E6), dont 3 tensions vraies
  (E1–E3, généralisées en « les étiquettes de statut dérivent entre deux
  réconciliations ») et 3 écarts assumés (E4–E6).
- **Portée.** Le CIR vaut pour ce que l'évidence couvre (le dépôt + la couche
  méta observée). Il ne généralise pas hors corpus. **Re-cadrage post-aveugle
  (0039, constat G)** : le sujet ne pré-engage pas de contenu — devant un
  problème neuf il ouvre le rite et arbitre ; le CIR prédit donc **ce que
  l'auteur validera au terme du rite** (par sélection, correction, arbitrage),
  plus que ce qu'il proposerait seul. Les prédictions de contenu non testées en
  aveugle (S1, S2, S4, S5) s'éprouveront en pratique, aux prochains grillings.
  Le CIR n'anticipe ni l'audit des skills (0040), ni la compilation.
- **Circularité surveillée.** Handoffs, cartes et ADR sont des condensés
  **interprétés** de l'auteur (ses mots) ; traités comme évidence de premier
  ordre mais jamais comme preuve de pratique lorsqu'un fait dur (git, mtime,
  code, mesure) pouvait trancher — c'est ce qui a permis E1/E2/Q3.
