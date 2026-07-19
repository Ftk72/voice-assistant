---
label: wayfinder:grilling
statut: clos
assigne: session-2026-07-20
bloque-par: []
carte: carte-graphe-memoire
---

# Correction ciblée des extractions

## Question

Gradué au grilling du 2026-07-18, qui **rouvre consciemment** une part du
hors-périmètre « édition du graphe » : sur l'esprit de l'apprentissage actif
(DiscoverText — l'IA pré-code, l'humain corrige), l'utilisateur doit pouvoir
**réparer ce que Graphiti a mal extrait**, depuis `/viz`. Borne actée au
grilling : **correction ciblée seulement** —

- corriger le **type** d'une entité (les huit types de `ontologie.py` — le
  « six » initial était une erreur, relevée à l'audit des prémisses) ;
- **invalider un fait/lien faux** (au sens Graphiti : `invalid_at`, pas de
  suppression physique — l'obsolescence est déjà le mécanisme validé par
  l'expérience « déménagement ») ;
- **renommer** une entité mal orthographiée.

La **fusion de doublons** et la **création manuelle de faits** restent hors
périmètre (l'assistant n'est pas un éditeur de graphe généraliste).

## Décisions du grilling du 2026-07-18 (tranché, reste à livrer)

Prémisses auditées en ouverture : le type d'entité n'existe **nulle part** dans
la chaîne aujourd'hui (`NoeudGraphe` sans champ type, corpus à
`labels: ['Entity']` nu, ticket 0026 non livré) et `GraphEdge` n'expose pas
l'`uuid` de l'arête au client.

- **Articulation avec 0026** : le 0029 pose la **plomberie** du type — champ
  `type` sur `NoeudGraphe`, `uuid` sur `GraphEdge`, types posés par le corpus,
  affichage sobre (texte) dans le panneau latéral. Le 0026 garde l'encodage
  *visuel* (formes/couleurs dans la scène).
- **Renommage** : `SET n.name` + **recalcul du `name_embedding`** (embedder
  8003) — sans lui, `/search` continuerait de raisonner sur l'ancienne
  orthographe. Les textes des faits (`r.fact`) restent **intacts** : citations
  historiques de l'extraction, jamais réécrites. Arêtes préservées par
  construction.
- **Invalidation d'un fait faux** : `invalid_at = valid_at` (repli
  `created_at`) — invalide **dès l'origine** : c'est une erreur d'extraction,
  pas une obsolescence ; la lecture temporelle (0027) ne le montrera jamais
  comme ayant été vrai. Jamais de suppression physique.
- **Annulation** : possible sur les invalidations **manuelles seulement**
  (la trace les distingue) ; les invalidations apprises par Graphiti restent
  intouchables.
- **API** : quatre routes `POST /corrections/{type,invalidation,renommage,annulation}`
  (body : uuid cible + nouvelle valeur), quatre méthodes sur le port
  `GraphMemory` (adaptateur factice pour le TDD + Graphiti). Pas de PATCH
  générique : la borne est de ne pas être un éditeur.
- **Trace** : propriétés posées sur l'élément corrigé — `corrige_le`
  (datetime), `corrige_geste` (`type|invalidation|renommage`), ancienne valeur
  (`nom_precedent` / `type_precedent`). Caveat assumé : la protection contre
  une ré-extraction est **contractuelle** (requêtable en un `WHERE`), pas
  encore appliquée dans le pipeline Graphiti — l'enforcement graduera si une
  ré-extraction réelle écrase un jour une correction.
- **UI** : tout dans le **panneau latéral existant** (prolonge le pattern
  « Oublier cette entité ») — sélecteur de type (8 types), crayon sur le nom,
  « marquer faux » par fait, badge « corrigé à la main le… », « annuler » sur
  les manuelles. Zéro geste nouveau dans la scène 3D.
- **Corpus** : le script pose les types sur toutes les entités et injecte
  **3 cas fautifs volontaires** (entité mal orthographiée, entité au mauvais
  type, fait faux), rejouables/purgeables (`corpus: "synthetique"`), sous
  contrat de test.

Jouable au navigateur sur le corpus synthétique — indépendant de la séance de
validation (0024).

## Critère de clôture

Les trois gestes (type, invalidation, renommage) actés au grilling et livrés
sous test côté serveur, jugés à l'œil dans `/viz` par l'utilisateur — fusion
et création manuelle restées dehors.

## Résolution

Livré et **validé à l'œil le 2026-07-20** sur la stack réelle (corpus
synthétique réinjecté). Tout ce qui était tranché au grilling est en place :

- **Plomberie du type et de l'uuid** : `NoeudGraphe` porte `uuid`/`type` +
  trace (`corrige_le`, `corrige_geste`, `nom_precedent`, `type_precedent`),
  `GraphEdge` porte `uuid` + trace ; `enrichir()` les préserve. Ajout par
  rapport au grilling : l'`uuid` sur `NoeudGraphe` aussi (les routes ciblent
  par uuid, le panneau devait avoir quoi envoyer).
- **API** : `POST /corrections/{type,invalidation,renommage,annulation}` —
  404 cible introuvable, 409 annulation d'une invalidation non manuelle,
  422 type hors des 8 ; 4 méthodes sur le port `GraphMemory` (factice pour le
  TDD + Graphiti en Cypher, liste blanche des types avant toute interpolation
  de label). Renommage : `SET n.name` + recalcul du `name_embedding` via
  l'embedder, textes des faits intacts. Invalidation :
  `invalid_at = coalesce(valid_at, created_at)`, jamais de suppression.
- **Corpus** : types posés sur toutes les entités (`TYPE_PAR_CHOSE` +
  personnes par défaut) et 3 cas fautifs sous contrat de test (`CAS_FAUTIFS` :
  « Aurlie Ferrand » mal orthographiée, « Rex » typé Personne, fait faux
  les reliant).
- **UI** : tout dans le panneau latéral (crayon ✎, sélecteur 8 types,
  « Marquer faux », badge « corrigé à la main le… » avec l'ancienne valeur au
  survol, « Annuler » sur les seules manuelles) ; les gestes n'apparaissent
  que sur les nœuds porteurs d'uuid (graphe complet — une exploration ciblée
  `/graph` n'en transporte pas). Zéro geste nouveau dans la scène 3D.

21 tests ajoutés (167 au total, verts). Caveat assumé au grilling maintenu :
la protection contre une ré-extraction est contractuelle (requêtable en un
`WHERE corrige_le IS NOT NULL`), pas appliquée dans le pipeline Graphiti.
Fusion de doublons et création manuelle restées dehors.
