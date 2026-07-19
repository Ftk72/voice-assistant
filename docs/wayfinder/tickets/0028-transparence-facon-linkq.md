---
label: wayfinder:grilling
statut: ouvert
assigne:
bloque-par: []
carte: carte-graphe-memoire
---

# Transparence façon LinkQ (interroger la mémoire sans halluciner)

## Question

Gradué au grilling du 2026-07-18 (recherche SOTA versée le même jour) :
poser une **question en français à la mémoire** et obtenir une réponse tirée
du **graphe réel**, jamais de la tête du LLM — sur le modèle de
[LinkQ](https://arxiv.org/abs/2406.06621) : le LLM traduit la question en
requête (Cypher chez nous), l'interface **montre le monologue intérieur**
(entités reconnues, requête générée) avant/pendant l'exécution, l'humain peut
corriger, et la réponse est formulée depuis les résultats vérité-terrain.
Une [étude de suivi](https://arxiv.org/abs/2505.21512) documente l'effet de
ces vues sur la confiance ; la famille neuro-symbolique
([KML](https://arxiv.org/abs/2503.14957)) pousse la même idée plus loin
(le LLM synthétise un programme, l'exécution est déterministe et traçable).

À trancher au grilling, puis livrer (la carte porte l'exécution) :

- **Le canal** : où vit la traduction français → Cypher (memory-forge,
  port ABC + adaptateur llama.cpp comme `GenerateurInsight` du 0020) et
  comment on borne les requêtes générées (lecture seule, garde-fous).
- **La vue** : quel « monologue intérieur » montrer dans `/viz` (entités
  reconnues, requête, résultats surlignés sur le graphe ?) et quel niveau de
  correction humaine (relire avant exécution, ou exécuter puis montrer ?).
- **La voix** : un outil MCP frère de `raconter_memoire` pour interroger la
  mémoire oralement — la réponse orale cite-t-elle ce qu'elle a trouvé ?
- **L'articulation avec le pilotage** (0025) : ce canal question → requête →
  entités est la brique que le pilotage LLM réutilisera pour faire voler la
  caméra — le contrat doit être partagé, pas dupliqué (d'où le blocage de
  0025 sur ce ticket).

Jouable dès maintenant au navigateur sur le corpus synthétique — ne dépend ni
de la coquille ni de la séance de validation (0024).

## Décisions (grilling du 2026-07-18)

Architecture actée, reste à livrer :

- **Canal hybride** : cinq gabarits Cypher écrits main et testés (que sait-on
  de X · lien entre X et Y, arête directe sinon plus court chemin · lecture
  temporelle valid_at/invalid_at · qu'est-ce qui touche au sujet S · combien
  de), repli **Cypher libre borné** si aucun ne colle. Aiguillage par **un
  seul appel LLM structuré** rendant du JSON (`{gabarit, paramètres}` ou
  `{cypher}`) — ce JSON est le monologue intérieur.
- **Ancrage anti-hallucination** : le LLM extrait les mentions d'entités, le
  serveur les **résout en flou** (casse, accents, sous-chaîne) contre les
  vrais noms de nœuds, en TDD sans LLM ; les mentions non résolues remontent
  au monologue au lieu d'entrer dans la requête.
- **Garde-fous du repli libre** : session Neo4j lecture seule, rejet des
  clauses d'écriture, `LIMIT` imposé, timeout.
- **Réponse française** : 2e appel LLM nourri exclusivement des résultats
  vérité-terrain (~18 s/question au total) ; les résultats bruts s'affichent
  à côté dans le monologue.
- **Vue** : exécuter puis montrer (tout est lecture seule, pas de validation
  préalable) ; requête **éditable et rejouable sans LLM** ; **surlignage +
  vol de caméra** vers les résultats via la mécanique de focus existante.
- **Contexte léger côté appelant** : service sans état, `POST /interroger`
  accepte un `contexte` optionnel (question précédente + entités résolues)
  fourni par la réponse précédente ; `/viz` le garde en variable JS.
- **Voix** : outil MCP `interroger_memoire(question)` dans ce ticket, même
  service, sourcing léger (« d'après N faits du graphe ») ; si rien n'est
  trouvé, le dire franchement.
- **Contrat 0025** : schéma pydantic de la réponse + fonction JS unique
  `appliquerVue(etat)` côté `/viz` (surlignage + vol) — la grammaire URL
  reste au grilling de 0025, rien d'anticipé.
- **Code** : port ABC + factice + adaptateur llama.cpp, modèle
  `GenerateurInsight` (0020).
- **Hors périmètre** : multi-tours complet avec historique de session,
  grammaire URL adressable, toute écriture sur le graphe par ce canal.

## Critère de clôture

Architecture et périmètre actés au grilling, et le rendu livré : une question
en français dans `/viz` produit une requête visible, exécutée sur Neo4j, et
une réponse sourcée par le graphe — validé à l'œil par l'utilisateur.
