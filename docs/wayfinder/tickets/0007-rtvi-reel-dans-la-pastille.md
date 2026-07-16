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
