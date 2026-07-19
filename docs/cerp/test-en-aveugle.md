---
label: cerp:predict
ticket: 0039-cerp-test-en-aveugle
cree: 2026-07-19
depend-de: [cir.md]
---

# CERP — Test en aveugle : le CIR prédit, l'ingénieur répond (ticket 0039)

> **Protocole tenu.** Prédictions rédigées **d'abord**, scellées hors du dépôt
> (SHA-256 `493601154b2913e81a849efeeda67f222cf8594e65cbfb1d76ecf416474d2d1f`,
> annoncée avant présentation des scénarios, re-vérifiée identique après les
> réponses). L'utilisateur a répondu **sans voir** les prédictions. HITL strict :
> aucune réponse n'a été soufflée. Six scénarios inédits + deux questions
> directes (Q7 et Q1-granularité, les deux points que le CIR n'avait pas pu
> trancher sur pièces).

---

## 1. Les scénarios soumis

| # | Scénario | Ce qu'il teste |
| --- | --- | --- |
| S1 | **Le bilan du soir** — capacité neuve : bilan vocal quotidien à 21 h | I2 (un seul cerveau), I7 (nommer), répartition des forges |
| S2 | **La panne intermittente** — 1 réponse sur 5 coupée en milieu de phrase, texte complet dans les logs | I1 (mesure, impasses d'abord), méthode maillon par maillon |
| S3 | **Le meilleur STT** — code Apache-2.0, poids « research only », 4 Go, torch nightly sm_120 non confirmé | I6 vs I5 : ordre des vétos |
| S4 | **Le doublon fantôme** — condition de course théorique, jamais observée | I1-b (garde-fou différé au constat) |
| S5 | **La main sur la maison** — agir par la voix sur le PC hôte | I3 (surface bornée), host-bridge, ADR |
| S6 | **Pipecat 2.0** — v2 qui casse l'API : migration progressive ou d'un bloc ? | I3/R1 (big bang si filet bon marché) |
| QD-1 | Qui a rédigé les 4 skills sur mesure ? | Q7 (indécidable sur pièces) |
| QD-2 | Qu'est-ce qui fait basculer bloc ↔ phase par phase ? | Q1 (granularité de validation) |

## 2. Les prédictions du CIR (texte scellé, intégral)

Reproduit tel quel depuis le fichier scellé (empreinte ci-dessus).

### S1 — Le bilan du soir

- **Cadrage prédit.** Il commencera par le vocabulaire : nommer le concept en
  français (« Bilan », « Bilan du soir » ou proche), vérifier le conflit avec
  CONTEXT.md (« Annonce » existe déjà — le bilan est-il une Annonce ?) avant
  toute architecture. (I7)
- **Heuristiques activées.** I2 (un seul cerveau), I7 (nommer d'abord),
  répartition par responsabilité des forges existantes.
- **Architecture préférée.** Aucune nouvelle forge. time-forge **déclenche**
  (échéance programmée, il exécute sans décider) ; **dialogue-forge compose** le
  contenu du bilan (c'est le cerveau : interroger memory-forge, formuler) ; la
  restitution passe par le canal d'annonces existant (Pont hôte/enceintes) ou la
  chaîne voix — mais la *décision du contenu* ne vit que dans dialogue-forge.
- **Compromis probable.** Réutiliser le canal d'annonces même si moins riche,
  plutôt qu'ouvrir un nouveau chemin audio. Pas de résumé pré-calculé stocké
  tant qu'un besoin ne se constate pas (I1-b).
- **Validation.** TDD adaptateurs factices d'abord ; clôture uniquement après un
  bilan **entendu au réel** à 21 h. (I1-a)
- **Rejets prédits.** Un second pipeline LLM dédié au résumé (I2) ; composer le
  bilan dans time-forge ; toute logique dans la coquille/le transport.

### S2 — La panne intermittente

- **Cadrage prédit.** D'abord **consulter `docs/impasses.md`** (mines connues
  sur la chaîne audio) ; puis délimiter le maillon fautif **par la mesure**,
  pas par l'impression. (I1 ; méthode « maillon par maillon » du 2026-07-16)
- **Méthode prédite.** Reproduire, puis instrumenter étage par étage jusqu'à
  voir **où** le contenu se perd. Suspecter aussi les fixes récents
  (NormaliseurWavPCM16, strip WAV) — croyance héritée à re-vérifier. (I1-a)
- **Priorités.** Localiser avant de corriger ; correction minimale déterministe.
- **Refus prédits.** Coder un retry/une rustine défensive avant que la cause ne
  soit **constatée** (I1-b) ; conclure sur une occurrence ; test de régression
  avant reproduction.
- **Capture.** Toute piste morte va dans `docs/impasses.md` à chaud (I8).

### S3 — Le meilleur STT

- **Prédiction centrale : refus, et le motif premier est la licence des
  poids.** « Research only » incompatible avec l'usage — même réflexe que
  l'écartement d'openWakeWord pour licence NC. **Licence > gain.** (I6)
- **Ordre des vétos prédit.** 1) licence des poids (éliminatoire), 2) torch
  nightly/sm_120 non prouvé (I5), 3) 4 Go = geste utilisateur, source vérifiée
  par API.
- **S'il explorait quand même** : extra optionnel isolé, test réel sm_120 avant
  toute déclaration, étiquette « jamais exécuté ».

### S4 — Le doublon fantôme

- **Prédiction centrale : il ne construit rien maintenant.** Motif ADR 0011 :
  aucun garde-fou tant que le problème « ne se constate pas ». (I1-b)
- **À la place** : un **point d'audit** (log/compteur déterministe rendant le
  doublon visible) ; consignation avec condition de réveil. (I8)
- **Si constaté un jour** : filtre déterministe, jamais un juge LLM. (I2)
- **Rejets prédits.** Dedup défensif immédiat ; réécriture « par prudence » ;
  test de régression d'un bug jamais reproduit.

### S5 — La main sur la maison

- **Cadrage prédit.** Vocabulaire d'abord : des **Commandes du catalogue**
  (ADR 0013), pas du code arbitraire — donc pas l'Atelier. (I7)
- **Architecture préférée.** dialogue-forge reconnaît l'intention (I2) ;
  exécution via **host-bridge** (seul pied hors Docker, ADR 0008), liste
  blanche argv étendue commande par commande.
- **Sécurité : par la surface, pas par l'auth.** Pas de token — la garde est
  dans la surface de l'API. (ADR 0013 ; I3)
- **Registre.** ADR probable, ou extension de l'ADR 0008. (I8)
- **Validation.** Au réel geste par geste, factice d'abord ; 2-3 commandes au
  départ, extension au constat (I1-b).
- **Rejets prédits.** Shell libre LLM sur l'hôte ; second service
  « intelligent » côté Windows ; sécurisation par token.

### S6 — Pipecat 2.0

- **Prédiction centrale : big bang, sans couche de compatibilité** — à
  condition qu'un **filet bon marché existe** (rester épinglé v1.5 tant que la
  migration n'est pas validée). L'assistant muet pendant la migration est un
  coût **assumé** : l'interruption de service est bon marché. (I3, R1, coût 3)
- **Ce qui le ferait basculer en progressif.** Rien de probable ici ; il a déjà
  refusé l'étranglement progressif recommandé. Couche de compat' = maintenance
  d'un compromis = plus cher que reconstruire.
- **Rejets prédits.** Fork de la v1.5 ; double chemin v1/v2 durable.

### QD-1 (= Q7)

**Prédiction : c'est l'agent qui a rédigé**, sur consignes et retours de
l'utilisateur, qui a relu/amendé — l'utilisateur auteur du *quoi*, l'agent du
*texte*. Confiance : moyenne.

### QD-2 (= Q1, granularité)

**Prédiction : la bascule suit la densité de décisions, pas le volume.** Lot
spécifié sans choix restants → bloc ; phase contenant un choix structurant →
grain fin. Secondaire : ce qui touche le réel se valide étape par étape.

## 3. Les réponses de l'utilisateur (verbatim, 2026-07-19)

> « Pour chacun des problèmes, j'aurais engagé un grilling avec toi pour que tu
> me conseilles sur la meilleure solution, avec une explication des trade-offs,
> puis j'aurais tranché.
> S3 : le deal breaker est le torch à refaire (nightly). J'aurais conservé le
> modèle [actuel].
> S6 : migration par couche.
> QD-1 : l'agent a rédigé les textes à ma demande, après un grilling.
> QD-2 : je penche pour ce qui me donne le plus de tâches AFK. »

## 4. Comparaison et score

Grille annoncée dans le fichier scellé : par dimension testable, **juste** (1) /
**partiel** (0,5) / **faux** (0). Les dimensions que la réponse ne teste pas
sont marquées **non testé** et sorties du dénominateur — pas comptées justes.

### Le constat G, avant tout score — la trouvaille majeure du test

À la question « comment décides-tu ? », le sujet ne répond **pas** par une
architecture : il répond par un **rite**. Pour les six scénarios, son premier
geste est identique — *ouvrir un grilling, exiger les trade-offs, trancher*.
C'est la confirmation la plus nette possible de **I4** (décider est un acte
verbal séparé de l'exécution ; l'humain tranche)… et en même temps une
**limite structurelle du protocole** : le CIR prédisait le **contenu** des
décisions, or le sujet ne pré-engage pas de contenu — le contenu émerge de la
dyade utilisateur+agent pendant le rite. Les invariants techniques du CIR
(I1–I3, I5–I8) décrivent donc pour partie **la doctrine que le sujet fait
appliquer** (par sélection, correction et arbitrage) plutôt qu'un plan qu'il
formule seul d'avance. Le CIR reste prédictif — mais son objet exact est
« ce que l'auteur validera », plus que « ce que l'auteur proposera ».

### Scores par item

| Item | Dimension testée | Prédit | Répondu | Score |
| --- | --- | --- | --- | --- |
| G (tous) | Processus de décision | grilling → trade-offs → l'humain tranche (I4, étape 3 du modèle §6) | exactement cela, énoncé spontanément pour les six scénarios | **1** |
| S1, S2, S4, S5 | Contenu (cadrage, architecture, rejets…) | — | non pré-engagé par le sujet (voir G) | **non testé** |
| S3 | Issue | refus / conservation de l'existant | conservation de l'existant | **1** |
| S3 | Motif premier | licence des poids éliminatoire (I6 devant I5) | **le torch nightly à refaire** — I5 (chaîne CUDA) devant I6 ; la licence n'est pas citée | **0** |
| S6 | Stratégie de migration | big bang avec filet, refus de la couche de compat' | **migration par couche** | **0** |
| QD-1 (Q7) | Origine des skills | rédigés par l'agent à la demande de l'utilisateur, après retours | « l'agent a rédigé les textes à ma demande, après un grilling » | **1** |
| QD-2 (Q1) | Critère de bascule | densité de décisions du lot | « ce qui me donne le plus de tâches AFK » | **0,5** |

**Score : 3,5 / 6 dimensions testables (58 %).** Lecture qualitative : le
**processus** (I4) et l'**attribution** (Q7) sont prédits exactement ; deux
prédictions **fortes** tombent (S6 big bang, S3 ordre des vétos) ; QD-2 est
partiel — le bon moteur de coût (son attention, la délégation bon marché),
le mauvais critère énoncé.

### Détail des trois écarts

- **Écart A (S6) — le big bang n'est pas une préférence, c'était un cas.** Le
  CIR généralisait l'ADR 0009 (« acceptera un big bang si filet bon marché »).
  Devant Pipecat 2.0, le sujet choisit la **couche de compatibilité** — l'option
  que le CIR prédisait rejetée. Relecture de l'évidence : dans l'ADR 0009, ce
  qui était jeté (OpenWebUI) était **abandonné**, pas mis à niveau ; le big bang
  y supprimait un composant entier. Ici Pipecat **reste** dans l'architecture.
  Hypothèse révisée : *big bang pour ce qu'on abandonne, progressif pour ce
  qu'on garde* — l'interruption de service n'est bon marché que quand elle paie
  une simplification définitive, pas une version.
- **Écart B (S3) — l'ordre des vétos était faux.** Le CIR plaçait la licence en
  filtre n° 1 (I6, appuyé sur openWakeWord). Le sujet nomme le **re-build de la
  chaîne torch/CUDA** comme deal breaker, sans mentionner la licence. La
  fonction de coût sous-estimait un poste : **refaire la chaîne CUDA sm_120**
  (post-traumatique des impasses de juillet) est un coût de premier rang, avant
  même l'examen de licence. I6 n'est pas réfuté (rien n'a été adopté qui le
  viole) mais son **rang de premier filtre** l'est.
- **Écart C (QD-2) — la bascule de granularité est « le plus d'AFK ».** Le
  critère réel maximise le **travail délégable en son absence**, pas la densité
  décisionnelle du lot. Cohérent avec la fonction de coût (attention chère,
  exécution délégable — coût n° 6) : la prédiction avait le bon moteur, le
  mauvais critère de surface. Q1 est désormais tranchée : la granularité de
  validation est réglée pour **maximiser l'AFK**, le HITL se concentrant aux
  bornes (grilling avant, vérification après).

### Questions du CIR tranchées par le test

- **Q7 : tranchée.** Les skills sur mesure ont été **rédigés par l'agent, à la
  demande de l'utilisateur, après un grilling**. La prédiction (confiance
  moyenne au CIR) est confirmée mot pour mot.
- **Q1 (marge de granularité) : tranchée** — critère « maximiser l'AFK »
  (écart C).

## 5. Révisions du CIR exigées par les écarts

1. **I3 — reformuler la clause big bang** (écart A) : remplacer « acceptera un
   big bang si un filet peu coûteux existe » par la distinction
   **abandon → big bang / montée de version d'un composant conservé →
   progressif**. Confiance de I3 : élevée → moyenne-élevée sur cette clause ;
   le reste de I3 (défaut inerte, enveloppe jetable) n'est pas touché.
2. **Fonction de coût — insérer un poste** (écart B) : « **refaire la chaîne
   CUDA/toolchain sm_120** » entre dans le haut du classement (au voisinage de
   la bande passante), et **passe devant l'examen de licence dans l'ordre des
   filtres** d'une dépendance de serving. I5 gagne ce que I6 perd en rang ; I6
   garde son statut d'axiome (véto), perd celui de premier filtre.
3. **Q1/Q7 — clore au §9** (écart C + QD-1) : Q7 tranchée (agent rédacteur sur
   demande, post-grilling — ce qui renforce aussi la note de circularité : les
   skills sont bien des condensés agent) ; Q1 tranchée : granularité =
   maximiser l'AFK.
4. **I4 — promouvoir, et re-cadrer la portée du CIR** (constat G) : I4 devient
   explicitement le **méta-invariant d'entrée** (tout problème neuf commence
   par le rite, avant même le nommage — l'étape 3 du modèle §6 remonte en
   étape 0) ; ajouter au §Portée que le CIR prédit **ce que l'auteur validera
   au terme du rite**, le contenu étant co-produit par la dyade.

**Ampleur jugée au score (brouillard de la carte) : retouche ciblée, pas de
seconde boucle Observe.** Les falsifications sont localisées (une clause de
I3, un ordre de filtres, un critère de Q1) ; le cœur du modèle (I1, I2, I4,
I6-véto, I7, I8, l'essentiel de la fonction de coût) sort confirmé ou
non-contredit du test.

## 6. Limites du protocole (à emporter en clôture de carte)

- **Le contenu est peu falsifiable en aveugle** : le sujet répondant par le
  rite, les prédictions de contenu (S1, S2, S4, S5) restent non testées — leur
  vraie épreuve sera la **pratique** (les prochains grillings réels diront si
  les propositions issues du CIR sont validées sans friction). Non compté
  comme succès.
- **Un seul passage, réponses courtes** : les écarts A/B reposent chacun sur
  une phrase — solides comme falsification (le sujet contredit frontalement la
  prédiction), faibles pour calibrer finement la révision.
- **Le testeur est aussi le co-auteur du corpus** (circularité assumée au CIR) :
  les scénarios ont été conçus par l'agent depuis le CIR — un biais de
  confirmation résiduel est possible sur ce qui a « confirmé ».
