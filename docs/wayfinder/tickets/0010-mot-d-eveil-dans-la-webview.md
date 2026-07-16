---
label: wayfinder:task
statut: ouvert
assigne:
bloque-par: [0003-run-reel-bout-en-bout, 0009-recherche-mot-d-eveil-francais]
---

# Mot d'éveil dans la webview

## Question

Intégrer le mot d'éveil français retenu par la recherche, **navigateur-side**
(ADR 0012 : l'audio ne quitte pas la webview en veille ; « rien ne quitte la
machine » poussé au processus) — bloqué par « Run réel bout-en-bout sur
Windows » (bouton d'abord : on n'empile pas deux inconnus, ADR 0012) et
« Recherche mot d'éveil français » :

- Détection continue dans la webview de la pastille (modèle vendoré local,
  zéro CDN) ; à la détection → même chemin d'ouverture de conversation que le
  bouton (l'établissement WebRTC existant, validé au run réel).
- Le mot d'éveil ouvre la conversation, il ne re-filtre **pas** chaque tour
  (glossaire *Conversation*, ADR 0012 décision 1).
- Mesurer en usage réel : faux positifs (télé, musique, conversations
  ambiantes), taux de détection à distance de pièce. Repli documenté si le
  modèle déçoit : bouton reste le chemin nominal, mot d'éveil custom
  (openWakeWord entraîné) en réserve SOTA de la roadmap.
- Critère de clôture (HITL final) : « dis… » ouvre une conversation réelle
  depuis la veille, pastille passant veille → écoute.
