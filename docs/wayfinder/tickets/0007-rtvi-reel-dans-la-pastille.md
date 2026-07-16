---
label: wayfinder:task
statut: clos
assigne: agent principal (implémentation inline, session 2026-07-16)
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

## Résolution (2026-07-16) — validé au réel

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

Validé à l'écran par l'utilisateur au run réel : chaîne voix complète
fonctionnelle (STT français parfait, TTFB 0,3-0,5 s ; réponse audio obtenue).
Seule réserve : **latence du premier tour à froid** (préfill LLM ~13 s, connu
handoff 0016) — à mesurer en régime pour le ticket 0011 (arbitrage latence,
cible ≤ 2 s). Le mapping RTVI (bâti sur les modèles Pipecat 1.5) est en place ;
la trace `RTVI: <type>` dans le journal de la console reste l'outil de contrôle
si un état diverge un jour.
