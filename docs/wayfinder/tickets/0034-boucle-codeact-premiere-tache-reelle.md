---
label: wayfinder:prototype
statut: clos
assigne:
bloque-par: [0031-contrat-de-l-action-forge, 0032-le-cerveau-tient-il-la-boucle, 0033-l-atelier-sandbox-jetable]
carte: carte-action-forge
---

# La boucle CodeAct et la première Tâche au réel

## Question

Le cœur du palier 1 : la boucle observe-réfléchit-agit de l'action-forge,
dans le mode d'action retenu par
[Le cerveau tient-il la boucle ?](0032-le-cerveau-tient-il-la-boucle.md),
sur l'Atelier livré en
[L'Atelier : la sandbox Docker jetable](0033-l-atelier-sandbox-jetable.md).

- **La boucle** (TDD, LLM factice d'abord) : énoncé de Tâche → pas d'Action
  dans l'Atelier → observation → itération → **Compte rendu** en français ;
  budget de pas borné, échec propre et racontable à la voix.
- **Prototype HITL** : l'utilisateur confie 2-3 Tâches réelles au texte
  (avant la voix) — « crée-moi un fichier qui…, convertis…, calcule… » — et
  juge le résultat et le compte rendu.
- Ce qui déçoit nourrit le brouillard (boucle longue du palier 2, politique
  réseau, expérience vocale).

## Livré le 2026-07-20

`app/boucle.py` : `BoucleCodeAct`, prompt système français (bloc ```bash``` =
une Action, `TERMINÉ: <compte rendu>` = clôture), observation
stdout/erreur/code retour réinjectée à chaque tour, budget de pas borné
(`ACTION_FORGE_BUDGET_PAS`, défaut 8), échec propre sur budget épuisé ou
`AtelierIndisponible` — jamais de boucle infinie. `app/llm/` : port
`MoteurLLM.completer` (un aller-retour texte, pas de streaming — le CodeAct
du 0032 est un seul appel par pas), `MoteurLLMFactice` (réponses scriptées,
défaut « rien à signaler » si épuisées) et `MoteurLLMOpenAI` (llama.cpp,
`stream: false`). `app/gestionnaire.py` : Tâches en mémoire, une Tâche = une
tâche asyncio dans son propre Atelier, file d'événements par Tâche pour le
flux SSE, annulation par `task.cancel()`. `app/routes.py` : `POST /taches`
(202), `GET /taches`, `GET /taches/{id}`, `POST /taches/{id}/annulation`,
`GET /taches/{id}/flux` (SSE) — conforme au contrat 0031, `/mcp` et l'UI
`/atelier` reportés au ticket 0035 (« au texte, avant la voix », donc `curl`
suffit ici). Nettoyage des Ateliers orphelins au démarrage
(`nettoyer_orphelins`, ADR 0013 § « Éphémère au palier 1 ») — smoke test réel
passé (conteneur orphelin créé à la main, détruit au redémarrage).

**Prototype HITL réel** (LLM 8001 + `AtelierDocker`, 2026-07-20) : 3 Tâches
en français confiées par `curl` — créer/relire un fichier, convertir une
température, créer un CSV puis calculer une moyenne. **3/3 réussies**, un
seul pas chacune, résultats numériques exacts (37,8 °C, moyenne 13,5),
comptes rendus en français corrects et naturels, aucun conteneur orphelin
laissé après coup. `MoteurLLMOpenAI` n'est donc plus « jamais exécuté à ce
jour ».

## Critère de clôture

Une Tâche énoncée en français aboutit dans l'Atelier et revient en compte
rendu jugé par l'utilisateur — la forge agit, au réel, en sandbox.
**Atteint le 2026-07-20** (3/3 Tâches HITL jugées correctes).
