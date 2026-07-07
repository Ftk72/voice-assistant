# ADR 0011 — Politique de mémoire de conversation : que mémorise-t-on, de qui, sous quelles conditions

Date : 2026-07-08 · Statut : accepté · Précise l'ADR 0005 (Graphiti/Neo4j) et l'ADR 0009 (architecture modulaire)

## Contexte

Le 2026-07-07, une hallucination de l'assistant capturée en épisode est
ressortie comme un **faux fait** via recall, forçant la purge complète du
graphe Neo4j (handoff 0011). Cause directe : l'orchestrateur confie à la
mémoire l'échange **à deux voix** (`"Utilisateur : … \n <persona> : …"`,
`dialogue.py`), ingéré en `EpisodeType.message`, dont Graphiti extrait des
faits **sans distinguer qui parle** — l'assistant est donc traité comme une
source de vérité au même titre que l'utilisateur.

Session de grilling du 2026-07-08 : décider *ce qu'on mémorise, de qui, et
sous quelles conditions*, avant tout branchement de la mémoire réelle (le
graphe est quasi vierge). Contraintes tenues tout du long : **déclaratif et
déterministe plutôt qu'un second LLM** (latence + nouvelle surface
d'hallucination), et **cohérence avec le glossaire** (mémoire ambiante,
provenance datée, frontière mémoire/agenda).

## Décisions

1. **L'utilisateur seul fait foi.** La mémoire ne tient ses faits que du tour
   **utilisateur** ; la parole de l'assistant n'est jamais ingérée. Ce que
   l'assistant sait du monde vient des outils (météo, web, agenda) avec leur
   provenance et n'a pas vocation à devenir un fait durable. C'est la réponse
   à la cause racine du faux fait.

2. **Capture du tour utilisateur brut, sans réécriture.** On n'ajoute pas de
   passe LLM de résolution de références. Les répliques courtes dépendantes du
   contexte (« oui exactement », « plutôt le mardi ») produisent peu ou pas de
   fait — ce qui est correct : l'information qu'elles confirment vient presque
   toujours de l'utilisateur plus tôt dans la conversation, déjà capturée. Un
   **filtre backchannels** (déterministe) saute purement la capture des tours
   sans information neuve (« oui », « ok », « merci », « d'accord »). On ne
   bâtira une réécriture que si une perte réelle se **constate**.

3. **Un épisode par conversation, ingéré à la fermeture.** On accumule les
   tours utilisateur et on n'ingère qu'à la fin de la conversation (veille du
   transport voix, ou changement de persona = nouvelle conversation). Justif :
   la conversation en cours vit **déjà dans le contexte du LLM** ; injection et
   recall ne servent qu'*entre* conversations. Différer la capture ne coûte
   donc aucun recall intra-session, tout en donnant des épisodes plus riches
   (extraction plus fiable sur le régime « épisode court » documenté en
   `ontologie.py`, relations inter-tours capturées) et bien moins d'appels
   d'extraction.

4. **Filtre de pertinence par l'ontologie, jamais par un juge LLM.** Ce qui
   mérite mémoire est décidé par les **types de nœuds déclarés** (déclaratif,
   déterministe, versionné, testable), pas par un LLM de tri à l'ingestion.
   Les états transitoires (« fatigué aujourd'hui ») ne s'accrochent à aucun
   type et retombent d'eux-mêmes.

5. **Ontologie : huit types de nœuds.** Aux trois existants (`Personne`,
   `Lieu`, `Activite`) s'ajoutent `Organisation`, `Animal`, `Bien`, `Projet`,
   `Aliment`. `Bien` est borné par un **test de durée** (« encore là et
   important dans un an ? » — véhicule, logement, instrument ; pas les
   consommables). `Projet` se distingue de la tâche d'agenda par **l'absence
   d'échéance datée**. `Aliment` couvre la zone la plus fréquente et la plus
   sensible (allergies + goûts culinaires). Les **relations** restent extraites
   en texte libre — on n'en déclare aucune.

6. **Frontière mémoire / agenda par nature, pas par présence d'une date.**
   Un **événement ponctuel qui attend son échéance** (rdv mardi) va à l'agenda
   (Time Forge) ; un **attribut durable** qui se trouve porter une date (« né
   le 3 mai », « a déménagé en 2019 ») va au graphe, la date n'étant qu'une
   propriété (`valid_at`/`invalid_at` de Graphiti). **Aucun type
   `Evenement`/`RendezVous` en mémoire.**

7. **Extraction silencieuse.** Les faits persistent sans confirmation de
   l'utilisateur — la mémoire est ambiante (glossaire, « Injection : sans
   intervention de l'utilisateur »). La confirmation sélective d'une classe à
   fort enjeu (santé/allergies, faisable via l'ontologie `Aliment`) est mise
   **en réserve**, à n'activer que si un faux fait santé se constate.

8. **Réparation par obsolescence + oubli + audit visuel.** On fait confiance à
   l'**obsolescence automatique** de Graphiti (une conversation ultérieure qui
   contredit un fait marque l'ancienne arête `invalid_at`, gardée en
   historique), rattrapée par l'**oubli vocal** (suppression réelle) et
   l'**audit du graphe 3D** `/viz` (repérer et oublier à l'œil). Aucun
   garde-fou déterministe « à valeur unique » n'est ajouté tant que la
   coexistence de doublons ne se constate pas. L'obsolescence Graphiti étant
   pilotée par LLM et jamais validée en réel, une **expérience « déménagement »
   est à mener tôt**.

9. **Off-record = zéro capture.** Une conversation menée sous un persona
   off-record (glossaire) ne déclenche aucune ingestion à la fermeture : rien
   n'est accumulé, rien n'est confié à la mémoire.

10. **Provenance = la conversation datée, pas le persona.** Puisque l'assistant
    ne fait pas foi, l'épisode est identifié par la conversation (datée), non
    par l'avatar qui répondait — cohérent avec le glossaire (« Provenance :
    conversation datée ») et avec les filtres de `/viz`.

Ces décisions portent sur la **mémoire de conversation**. L'ingestion de
**documents** (memory-forge `ingest/`, provenance `document`, source qui fait
foi par nature — ADR 0006) est un autre canal, **inchangé**.

## Conséquences

- **dialogue-forge** : la capture passe de per-tour (`jouer_tour`) à
  **per-conversation**. Nouveau point d'entrée « clore la conversation »
  (accumulation des tours utilisateur, contenu **user-only**, skip off-record),
  déclenché à terme par le transport voix (front A2) ; en attendant, un
  `POST /conversation/clore` explicite débloque. Le filtre backchannels vit
  côté orchestrateur.
- **memory-forge** : `ontologie.py` passe à huit types ; le nom d'épisode /
  la provenance s'alignent sur la conversation datée. La visualisation `/viz`
  et l'oubli deviennent la **surface d'audit** de premier plan (déjà livrés,
  front B1) — leur importance monte d'un cran.
- **CONTEXT.md** : les termes *Épisode* et *Provenance* se précisent (épisode
  = tours utilisateur d'une conversation ; provenance = conversation datée) ;
  le glossaire mémoire gagne les huit types comme vocabulaire de faits.
- **Prémisse à lever tôt** : valider en réel l'obsolescence Graphiti
  (« j'habite Paris » puis, autre conversation, « déménagé à Lyon » →
  l'arête Paris passe-t-elle `invalid_at` ?) — jamais exécuté à ce jour.
- **Épisodes de test** : mémoire factice dans les bancs (leçon de la pollution
  du graphe, handoff 0011).

## Alternatives écartées

- **Ingérer les deux voix avec provenance par locuteur** : le faux fait entre
  quand même, seulement étiqueté ; alourdit l'ontologie sans traiter la cause.
- **Juge LLM de pertinence à l'ingestion** : latence, non déterministe (donc
  non testable), nouvelle surface d'hallucination — contraire à la ligne
  « déclaratif plutôt qu'un second LLM ».
- **Réécriture des références avant ingestion** (résoudre « oui exactement »
  en énoncé autoportant) : second appel LLM par tour + risque de déformation ;
  différé jusqu'à preuve d'une perte réelle.
- **Un épisode par tour** : épisodes les plus courts (extraction la plus
  fragile), relations inter-tours perdues, plus d'appels d'extraction — sans
  gain, la conversation en cours étant déjà dans le contexte du LLM.
- **Type large `Sujet`/`Chose`** pour toutes les cibles de préférence :
  réintroduit le flou « nom générique » que le typage devait tuer, aspire trop
  de nœuds.
- **Extraction confirmée systématique** : tue la mémoire ambiante, impose un
  rituel de clôture pénible.
- **Garde-fou déterministe « slot à valeur unique »** dès maintenant : sort du
  modèle Graphiti, vrai chantier, prématuré tant que le double n'est pas
  constaté et que `/viz` + oubli couvrent déjà le pire cas.
- **Tout le daté en mémoire** : doublonne l'agenda et brouille les deux forges.
