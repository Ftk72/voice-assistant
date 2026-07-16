---
label: wayfinder:task
statut: clos
assigne: subagent-sonnet (délégation du 2026-07-10, session carte)
bloque-par: []
---

# Expérience déménagement

## Question

Valider **en réel** l'obsolescence Graphiti — pilier de l'ADR 0011 (décision 8)
jamais exécuté (AFK : tout se joue en API, l'agent peut le faire seul avec la
stack Docker debout) :

- Conversation A via l'API du Dialogue Forge : tours utilisateur contenant
  « j'habite à Paris » → `POST /conversation/clore` → attendre l'extraction
  différée → vérifier le fait dans le graphe (arête habite→Paris, `valid_at`).
- Conversation B (nouvelle, plus tard) : « j'ai déménagé à Lyon » → clôture →
  extraction → **l'arête Paris passe-t-elle `invalid_at`** (obsolète, gardée
  en historique) pendant que Lyon devient le fait courant ?
- Contrôler dans Neo4j (Cypher) et dans `/viz` (les faits obsolètes estompés).
- Au passage : premiers faits réels vus par l'**ontologie à 8 types**
  (`Personne`, `Lieu`…) — noter tout typage aberrant.

Résolution = verdict factuel oui/non + preuves (requêtes, captures). Si
l'obsolescence ne fonctionne pas : le fog s'épaissit (garde-fous ADR 0011 mis
« en réserve » à re-grillinger) — nouveau ticket à créer, pas de fix improvisé.

## Résolution (2026-07-10)

**OUI — l'obsolescence bi-temporelle Graphiti fonctionne en réel** (ADR 0011
décision 8 validée). Preuves : « habite à Paris » (conv. A, `valid_at`
10:16:13Z) passé `invalid_at: 10:18:50Z` = l'instant exact du `/clore` de la
conv. B « habite à Lyon » (fait courant, `invalid_at: null`) ; invalidation
transitive correcte du « 14e arrondissement » ; rien de supprimé (historique
conservé) ; recoupé par Cypher direct dans Neo4j. Extraction en ~26-84 s après
`/clore`. Typage ontologique impeccable (`Personne`/`Lieu`), résolution
d'entités saine (nœud « Utilisateur » réutilisé entre conversations, pas
dupliqué). L'injection mémoire a même fonctionné en passant (la conv. B savait
pour Paris).

Découvertes annexes :
- **Image du conteneur `memory` périmée** (4 jours) : `/graph/complet` et
  `/viz` sont dans le code mais 404 dans le conteneur → rebuild à lancer par
  l'utilisateur (`docker compose build memory && docker compose up -d memory`).
- Le nœud Personne s'appelle littéralement « Utilisateur » (conséquence ADR
  0011 décision 1) — vigilance fusion le jour où le vrai prénom sera donné.
- Graphe laissé en l'état (Paris invalidé + Lyon) : matière d'audit pour /viz.
