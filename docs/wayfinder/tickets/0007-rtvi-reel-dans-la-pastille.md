---
label: wayfinder:task
statut: ouvert
assigne:
bloque-par: [0003-run-reel-bout-en-bout]
---

# RTVI réel dans la pastille

## Question

Passer la pastille du **stub visuel** aux **événements RTVI réels** de Pipecat
(états veille/écoute/parle, déclenchement manuel de la conversation) — bloqué
par « Run réel bout-en-bout sur Windows », qui aura observé les événements
RTVI réellement émis (noms, timing, payloads : différée ADR 0012 levée).

- Client RTVI JS dans la webview de la pastille (vendoré, pas de CDN —
  souveraineté), branché sur le transport SmallWebRTC.
- États affichés fidèles au cycle de conversation ADR 0012 (ouverture bouton,
  fenêtre d'écoute de suite, fin par silence/arrêt → retour veille).
- Aucune logique métier dans la coquille (ADR 0009) : la pastille écoute et
  affiche, elle ne décide rien.
- Critère de clôture : cycle complet visible sur la pastille pendant une
  conversation réelle (HITL final court pour la vérification à l'écran).

## État (2026-07-16) — implémenté, en attente de vérification à l'écran

Débloqué : 0003 confirmé au réel par l'utilisateur (« ça marche et ça répond »).
Implémentation livrée (option **console lit, relaie à la pastille** — la
connexion WebRTC et le canal `pipecat` vivent dans la console, pas la pastille) :

- `coquille/src/console.js` : lecture du canal de données, mapping des
  événements RTVI Pipecat 1.5 (`bot-started-speaking`→parle ;
  `bot-stopped-speaking`/`bot-interrupted`/`bot-ready`/`user-*-speaking`→écoute)
  vers un événement Tauri `etat-pastille` ; `veille` au raccrochage.
- `coquille/src/pastille.js` : stub-clic remplacé par un écouteur de
  `etat-pastille` (la pastille n'affiche plus rien qu'elle décide — ADR 0009).
- `tauri.conf.json` : `withGlobalTauri: true` (accès `window.__TAURI__.event`
  depuis les scripts). Permission déjà couverte par `core:default`
  (⊇ `core:event:default`). `pastille.html` : `<button>`→`<div>` (affichage seul).

Format du fil **groundé sur le Pipecat 1.5.0 installé** (pas deviné) :
`{label:"rtvi-ai", type, id, data}` envoyé brut par `send_app_message`.

Reste (HITL, à l'écran, après relance de la coquille) : confirmer que les états
défilent fidèlement pendant une conversation, et **relever les types RTVI
réellement émis** (le mapping est bâti sur les modèles Pipecat, à valider en
direct). Toute divergence → correctif ici + note `docs/impasses.md`.
