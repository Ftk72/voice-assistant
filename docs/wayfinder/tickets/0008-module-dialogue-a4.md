---
label: wayfinder:task
statut: clos
assigne: agent principal (session 2026-07-17) + utilisateur (HITL, poste Windows)
bloque-par: [0007-rtvi-reel-dans-la-pastille, 0004-voix-du-flux-appliquee-par-tour]
---

# Module dialogue (A4)

## Question

Livrer le **module d'interface du dialogue** (front A4 de la roadmap) : suivre
une conversation vocale depuis la console — le fil des phrases, le persona
pilote, la voix dérogée, les outils appelés — sans jamais mettre de logique
métier côté coquille (ADR 0009). Débloqué : 0007 (RTVI réel, validé 2026-07-16)
et 0004 (voix du flux par tour) sont clos.

## Prémisses vérifiées (audit 2026-07-17)

- **Le Dialogue Forge existe** (`dialogue-forge/`, FastAPI, pattern des forges).
  Le « dialogue-forge à naître » du CLAUDE.md est **stale** — à corriger.
- **Le DF ne sert aucune UI** : aucun `StaticFiles`/`mount`/template dans
  `app/main.py`. Toute la page est à bâtir, sur le modèle voice-forge `/admin`
  et memory-forge `/viz` (chaque forge sert sa propre UI).
- **Surface REST déjà en place** (`app/routes/api.py`), réutilisable telle
  quelle par l'UI :
  - `GET /personas` → `[{nom, voix}]` (menu persona) ;
  - `POST /conversations` (persona optionnel) → `{id}` ;
  - `GET /conversations/{id}` → `{id, persona, historique}` (rejeu du fil) ;
  - `POST /conversations/{id}/tours` → **flux NDJSON** d'événements de
    l'orchestrateur (phrases, appels d'outils) ;
  - `POST /conversations/{id}/interrompre`, `POST …/clore`.
- **Dérogation de voix : endpoint manquant.** `TourIn` n'a pas de champ voix ;
  aucune route ne dérogeant la voix pour la conversation en cours. À créer côté
  DF (l'effet moteur — `TTSUpdateSettingsFrame` avant chaque phrase — est déjà
  livré par 0004, côté transport).

## Premises résolus (2026-07-17, sur Pipecat 1.5 installé + code DF)

- **Source du texte de conversation = canal RTVI** (déjà lu par `console.js`,
  résolution 0007), pas le NDJSON `/tours`. Types portant le texte, avec le
  timing de lecture :
  - `user-transcription` (`data.text`, `data.final` — STT batch = `final:true`) ;
  - `bot-tts-text` (texte par segment TTS, au fil de la synthèse) et
    `bot-transcription` (énoncé assistant agrégé) ;
  - états : `bot-started-speaking` / `bot-stopped-speaking` / `bot-interrupted`.
  Le `RTVIObserver` par défaut de `PipelineWorker` les émet (pipecat.py:130).
- **Indicateur d'outils appelés : aucune source aujourd'hui.** Le DF remplace
  l'étage LLM (`dialogue_processor.py`), donc les `llm-function-call-*` RTVI ne
  se déclenchent **jamais** ; et le flux NDJSON `/tours` du DF n'émet que
  `phrase`/`fin` — l'appel d'outil (`dialogue.py`) est interne, sans yield.
  → **Travail DF requis** : émettre des événements d'outil dans le flux (et les
  faire remonter jusqu'à l'UI). Option probable : le transport pousse un
  `RTVIServerMessage` (`RTVI.ServerMessage`, observer) pour unifier sur le canal
  RTVI. À décider avec la tension ci-dessous.

## Décision à trancher à l'ouverture (tension d'architecture)

Les phrases doivent s'afficher **au moment où leur synthèse est jouée** (RTVI,
ADR 0010 décision 5 ; les phrases interrompues jamais affichées). Or les
événements RTVI vivent dans la **console de la coquille** (`console.js` lit le
canal `pipecat` et relaie `etat-pastille` — résolution de 0007), **pas** dans
une page servie par le DF. Deux montages possibles :

1. **Page DF chargée en onglet console**, alimentée par le REST du DF pour le
   contenu statique (personas, historique, dérogation voix) + les événements
   RTVI relayés depuis `console.js` (comme la pastille reçoit `etat-pastille`).
   Respecte « chaque forge sert son UI » ; la coquille ne fait que relayer.
2. **UI intégrée à la console** (`console.js`/`console.html`), qui détient déjà
   le canal RTVI. Plus simple, mais met de l'affichage-conversation dans la
   coquille — à cadrer pour rester « affiche, ne décide pas » (ADR 0009).

Recommandation : **option 1** (cohérente ADR 0009), avec le relais RTVI
console→page par événement Tauri, comme 0007. À confirmer via `/premisses` sur
la forme réelle des événements RTVI portant le **texte** des phrases (le canal
observé en 0007 portait les états veille/écoute/parle ; reste à vérifier qu'un
événement porte la transcription assistant phrase par phrase, sinon la source
du texte est le flux NDJSON `/tours` corrélé au timing RTVI).

## Avancement (session 2026-07-17)

Architecture retenue : **option 1** (page DF servie, chargée en iframe dans la
console, fil relayé par `postMessage` — la coquille ne fait que relayer).
DF **43 tests verts, ruff clean**.

- ✅ **Dérogation de voix** (TDD) : `DerogationVoix`, `POST /conversations/{id}/voix`
  → `{voix}`, état `voix_derogee` par conversation, `Orchestrateur.jouer_tour(
  ..., voix=)` porte la voix dérogée (effet au tour suivant). 404 si inconnue.
- ✅ **Page du module** servie par le DF (`app/routes/module_dialogue.py`,
  assets `app/module_dialogue/`) : menu persona (change = nouvelle conversation),
  menu voix (déroge, v1 = voix distinctes des personas), rejeu de l'historique
  (`GET /conversations/{id}`), fil vif alimenté par `postMessage` RTVI
  (`user-transcription` final, `bot-tts-text` au fil de la synthèse,
  `bot-interrupted` fige la bulle), placeholder outils. Tests de service.
- ✅ **Émission des événements d'outil** dans le flux DF (TDD) :
  `{"type":"outil","nom":...}` à chaque appel — source de l'indicateur d'outils
  (le transport ignore ce type inconnu, rest.py, donc sans risque).
- ✅ **Coquille** : iframe DF dans `index.html`, relais RTVI complet dans
  `console.js` (`relayerAuDialogue`, ciblé sur l'origine DF), CSP
  `frame-src http://127.0.0.1:8600` ajoutée (sinon iframe refusée en silence).

- ✅ **Relais des outils DF → console** (maillon complet, TDD côté testable) :
  `dialogue/base.py` (`AppelOutilVu`) + `rest.py` (décodage `{"type":"outil"}` →
  `AppelOutilVu`, testé sans réseau via `httpx.MockTransport`) + le processeur
  pousse un `RTVIServerMessageFrame(data={kind:"outil-appele",nom})` (test
  pipecat, sauté hors Windows) ; le `RTVIObserver` l'émet en `server-message`
  (label `rtvi-ai` vérifié) → `console.js` le relaie tel quel → la page mappe
  `server-message`/`kind` vers l'indicateur. Transport : **23 tests + 2 sautés
  (pipecat), ruff clean**.

### Canal de commande page ↔ conversation live (décision 2026-07-17)

Trou révélé à l'audit : la page et le transport créaient **deux conversations DF
distinctes** — les menus de la page ne commandaient donc pas la voix live.
Résolu par un canal bidirectionnel (option « canal de commande complet ») :

- **Enabler 1 — transport → page** : à la création de sa conversation, le
  processeur pousse un `RTVIServerMessage {kind:"conversation", id, persona}` ;
  la page **adopte** cet id (`adopterConversationLive`) et vise dès lors la
  conversation live pour la **dérogation de voix** (REST DF même origine) et le
  **rejeu d'historique**. La conversation « fantôme » créée à l'amorçage ne sert
  plus que de repli en usage isolé. TDD : `test_l_id_de_conversation_est_publie`.
- **Enabler 2 — page → transport (persona)** : la page remonte une commande à la
  console (`postMessage {source:"commande"}`) ; la console l'émet en **RTVI
  client-message** `{t:"persona", d:{nom}}` sur le canal ; le transport la reçoit
  via un `RTVIProcessor` explicite (`on_client_message`, passé à `PipelineWorker(
  rtvi_processor=)` qui le prépend) et appelle `changer_persona` → conversation
  recréée, nouvel id republié (Enabler 1 rejoue). TDD :
  `test_changer_persona_recree_une_conversation_neuve`.

Parts **jamais exécutées** (validées seulement au run réel) : le `RTVIProcessor`
custom et son `on_client_message`, le format filaire du client-message, le
relais montant de la console. Le reste est couvert en unitaire (pipecat sur
Windows, page en navigateur).

Toutes les briques sont en place. Il ne reste que la **validation au run réel**.

**Validé en navigateur isolé (2026-07-17)** : page servie, menus persona/voix,
rejeu, fil vif (transcription utilisateur, phrases assistant au fil de la
synthèse, `bot-interrupted` fige la bulle) et indicateur d'outils — tous
exercés via un `postMessage` RTVI simulé dans la console devtools. Seul le
câblage vif reste à prouver au run réel (iframe WebView2 + relais RTVI live).

### À vérifier au run réel (HITL)

- Le cadrage iframe cross-origin `tauri://` → `127.0.0.1:8600` sous WebView2
  (la CSP est ouverte ; reste le comportement réel du moteur).
- Le `postMessage` console→iframe traverse bien (origines, timing de chargement).
- Les payloads RTVI réels (`bot-tts-text.text`, `user-transcription.final`)
  conformes aux modèles Pipecat 1.5 lus ici.
- Le round-trip du `server-message` d'outil (le `RTVIServerMessageFrame` poussé
  par un `FrameProcessor` intermédiaire est bien relayé par l'observer) — les
  tests pipecat le couvrent en structure, le run réel le prouve en vrai.

## Périmètre

- Page web servie par le DF (route + statiques, pattern `/admin`) :
  - **encadré de conversation** : phrases affichées au fil de la lecture TTS ;
    transcriptions utilisateur après leur tour (STT batch) ; phrases
    interrompues jamais affichées ;
  - **menu persona** (pilote) — changer = nouvelle conversation
    (`POST /conversations`) ;
  - **menu voix** (déroge pour la conversation en cours, effet au tour suivant)
    — via le nouvel endpoint de dérogation ;
  - **historique du fil** (`GET /conversations/{id}`) ;
  - **indicateur d'outils appelés** (événements d'outil du flux NDJSON).
- Côté DF : **endpoint de dérogation de voix** (route + schéma + orchestrateur),
  en TDD ports/adaptateurs (pattern memory-forge).
- Correction doc : le CLAUDE.md ne doit plus dire « dialogue-forge à naître ».

## Critère de clôture

Une conversation vocale complète est **suivie depuis la console** : phrases
assistant au fil de la lecture (jamais les interrompues), transcriptions
utilisateur après leur tour, persona et voix pilotés depuis les menus (voix
dérogée effective au tour suivant), outils appelés visibles. Vérification HITL
courte au poste Windows.

## Résolution (2026-07-17) — validé au réel, les 4 critères passent

Le module d'interface du dialogue est **livré et validé au poste Windows**
(« ok tout fonctionne ») : conversation vocale suivie depuis la console, fil au
timing de synthèse, menus persona/voix pilotant la conversation **live**,
indicateur d'outils. Le critère de clôture est atteint intégralement — y compris
le pilotage par menus, qui a exigé le canal de commande (ci-dessous).

**Ce qui a été livré** — DF 43 tests verts, transport 23 + 2 sautés (pipecat),
ruff clean partout :

- **Page servie par le DF** (`app/routes/module_dialogue.py`, assets
  `app/module_dialogue/`), chargée en iframe dans la console — ADR 0009 tenu :
  la coquille ne fait que relayer, aucune logique métier.
- **Dérogation de voix** : `POST /conversations/{id}/voix`, état `voix_derogee`,
  `Orchestrateur.jouer_tour(..., voix=)` — effet au tour suivant.
- **Événements d'outil** dans le flux DF (`{"type":"outil","nom":…}`), relayés
  par le transport en `RTVIServerMessage` jusqu'au pied de page.
- **Canal de commande bidirectionnel** (le trou trouvé à l'audit : page et
  transport tenaient deux conversations DF distinctes, donc les menus ne
  commandaient rien) : le transport publie l'id de sa conversation, la page
  l'adopte ; la page remonte le changement de persona par la console en RTVI
  client-message, le transport recrée sa conversation et republie l'id.
- **Coquille** : iframe, relais RTVI descendant/montant, CSP `frame-src`.

**Ce que le run réel a révélé** (aucun défaut du module — tout venait de
l'environnement) : `docker compose up --build <service>` reconstruit tout l'arbre
`depends_on` et a réveillé `chatterbox` (20 min de build), dont la pression
mémoire a fait **paginer le LLM** — débit tombé à 0,9 tok/s contre ~33 de
référence, ce qui se présentait comme « le modèle ne répond pas / est très
lent ». Les deux pièges sont au registre (`docs/impasses.md`, 2026-07-17) ;
la topologie Windows sourcée en cours de route (chemin `\\wsl.localhost`,
PowerShell 5.1 sans `&&`, état requis, `--extra pipecat`) est passée au
CLAUDE.md — elle était jusqu'ici enterrée dans le §Setup du handoff 0014.

**Mesures** : STT TTFB 0,3-0,6 s, traitement STT 0,1-0,4 s, LLM en régime
28-36 tok/s (conforme à la référence 33). La latence voix→voix en régime reste
à mesurer proprement — c'est l'objet du ticket 0011.

**Reste ouvert, hors périmètre de ce ticket** : le menu voix ne liste que les
voix distinctes des personas (v1) ; la liste complète des voix enrôlées, servie
par voice-forge, demande un accès cross-forge à cadrer.
