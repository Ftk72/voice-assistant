---
label: wayfinder:prototype
statut: clos
assigne:
bloque-par: [0034-boucle-codeact-premiere-tache-reelle]
carte: carte-action-forge
---

# L'action à la voix (lancer, continuer, être prévenu)

## Question

Brancher le palier 1 sur la conversation : une Tâche se **lance à la voix**
(outil MCP de l'action-forge exposé au Dialogue Forge), la conversation
**continue pendant** que l'Atelier travaille, et la fin **s'annonce** —
le précédent est le minuteur de time-forge (annonce à l'échéance).

Prototype HITL, à trancher en jouant :

- L'énoncé : comment le Dialogue Forge reconnaît une Tâche d'action et la
  formule à la forge (et ce qu'il répond immédiatement : « je m'y mets »).
- Le pendant : silence, ou point d'étape si on le demande (« où en es-tu ? ») ;
  le compte rendu final restitué oralement, jamais lu ligne à ligne.
- Le visible : la Tâche et son état dans la coquille (module d'interface servi
  par l'action-forge, pattern voice-forge `/admin`) — la coquille assemble,
  sans logique métier.

## Livré le 2026-07-20

`app/mcp_server.py` : trois outils MCP à description orientée voix —
`confier_tache` (lance la Tâche et **rend la main immédiatement** : « Je m'y
mets », le LLM est explicitement dissuadé d'attendre ou de promettre un
résultat), `ou_en_est_la_tache` et `annuler_tache`, qui **visent par défaut la
Tâche en cours la plus récente** (l'utilisateur ne prononce jamais un
identifiant à voix haute — d'où `GestionnaireTaches.derniere_en_cours()`).
Monté sur `/mcp` (`stateless_http=True`, `allowed_hosts` incluant
`action:8800`), catalogue chargé par le Dialogue Forge via `mcp_urls`.

`app/annonce/` : port `Annonceur` + `AnnonceurJournal` (défaut, tests) +
`AnnonceurPontHote` (voice-forge → Pont hôte, ADR 0008) — la fin de Tâche
s'annonce comme l'échéance d'un minuteur. Branché dans
`GestionnaireTaches._annoncer_issue` : annonce sur `terminee` / `echouee`,
**jamais sur `annulee`** (l'utilisateur vient de la demander), et une annonce
en échec n'empêche jamais la Tâche de se conclure (sous test).

`app/atelier_ui/index.html` servi en `GET /atelier` (pattern voice-forge
`/admin`, zéro ressource externe) : liste des Tâches, journal en direct via le
SSE existant, bouton d'annulation. La coquille n'assemble que.

**Écueils rencontrés à la validation, consignés dans `docs/impasses.md`** :
(1) `scripts/demarrage-hote.sh` est muet par construction (`exec >>` vers son
journal) et paraît figé ; il ne rebuild pas, si bien qu'une forge modifiée
repart sur son ancienne image — le Dialogue Forge, qui charge son catalogue
d'outils au démarrage **sans tolérance à l'échec**, est alors mort en boucle
sur `McpError: Session terminated` (un `depends_on: service_healthy` ne
protège de rien, `/health` répondant `ok` sur une image périmée) ;
(2) le service `action` n'avait **pas** de `ACTION_FORGE_LLM_BACKEND` dans le
compose → moteur factice, Tâches « terminées » avec un journal vide et une
annonce nominale : échec silencieux et plausible (le HITL du 0034 avait été
joué avec un override jamais versionné). Corrigé (`LLM_BACKEND: openai`,
`LLM_BASE_URL: http://llm:8080/v1`, `depends_on: llm`).

`AnnonceurPontHote` n'est donc plus « jamais exécuté à ce jour ».

**Deux tickets correctifs ouverts sur ce qu'a révélé la validation** (aucun ne
remet en cause le palier 1, atteint) :
[Le Dialogue Forge survit à une forge d'outils absente](0043-le-dialogue-survit-a-une-forge-absente.md)
et [L'assistant s'entend et se répond](0044-l-assistant-s-entend-et-se-repond.md)
— l'annonce sortie par le Pont hôte est rentrée par le micro de la coquille
restée ouverte, et l'assistant a répondu à sa propre voix.

## Critère de clôture

Une Tâche confiée à la voix aboutit et s'annonce, jugée à l'oreille et à
l'œil par l'utilisateur au poste Windows — le palier 1 de la destination est
atteint. **Atteint le 2026-07-20** : Tâche énoncée à la voix dans la coquille,
« je m'y mets » immédiat, conversation poursuivie pendant le travail, compte
rendu annoncé sur les enceintes et Tâche suivie dans `/atelier`. Boucle réelle
vérifiée en parallèle au `curl` (2 pas : `seq 1 20 > nombres.txt` puis somme
en Python → 210 exact, compte rendu français correct).
