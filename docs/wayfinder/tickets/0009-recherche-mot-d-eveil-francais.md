---
label: wayfinder:research
statut: clos
assigne: subagent-sonnet (relance du 2026-07-10)
bloque-par: []
---

# Recherche mot d'éveil français

## Question

Le risque ouvert de la roadmap depuis l'ADR 0009 : **existe-t-il un modèle de
mot d'éveil français utilisable navigateur-side**, et lequel ? (AFK, recherche
documentaire — budget téléchargement subagent 3 Go si un modèle doit être
essayé localement.)

- **openWakeWord** : modèles français communautaires disponibles ? Qualité
  rapportée (faux positifs) ? Entraînement custom (piper-sample-generator) —
  coût réel pour un « dis Emma »/mot choisi par l'utilisateur ?
- **Contrainte d'exécution** : ADR 0012 décision 2 — le mot d'éveil tourne
  **dans le navigateur** (WebView2), l'audio ne quitte pas la webview en
  veille. openWakeWord est Python/ONNX : quelle voie navigateur
  (onnxruntime-web/WASM vendoré ? modèle converti ?) — ou faut-il réviser
  cette contrainte (à re-grillinger si oui, pas à trancher seul) ?
- **Alternatives souveraines** à comparer honnêtement : porcupine (licence ?),
  Vosk keyword spotting, micro-modèles WASM dédiés. Tout cloud exclu d'office.
- Vérifier dépôts/tags via API avant de donner toute commande de
  téléchargement (CLAUDE.md).

Résolution = note markdown liée (candidat retenu + voie d'intégration
navigateur + plan B), qui débloque « Mot d'éveil dans la webview ».

## Résolution (2026-07-16, vérifiée par l'agent principal)

Note complète : [`docs/wayfinder/notes/recherche-mot-d-eveil-francais.md`](../notes/recherche-mot-d-eveil-francais.md).

- **Recommandation : openWakeWord + portage web `openwakeword_wasm` (vendoré
  comme code interne, ~19 Mo), avec mot d'éveil français ENTRAÎNÉ SUR MESURE**
  — aucun modèle FR prêt à l'emploi n'existe, mais le chemin d'entraînement
  est balisé (Piper `fr_FR-upmc-medium`, notebook Colab officiel, pratique
  communautaire Home Assistant).
- **Plan B** : rester au bouton (V1 actée ADR 0012) si le mot maison déçoit ;
  réévaluer sherpa-onnx si un modèle KWS FR officiel apparaît.
- **Écartés** : Porcupine (AccessKey à validation réseau périodique —
  contraire ADR 0007) ; sherpa-onnx (WASM le plus mûr mais zéro modèle FR,
  BPE anglais en approximation phonétique non documentée) ; Vosk (pas de voie
  KWS navigateur crédible).
- Risque assumé à trancher à l'intégration : le portage web n'a qu'un
  mainteneur et 8 commits — d'où le vendoring interne audité plutôt qu'une
  dépendance vivante.

Débloque « Mot d'éveil dans la webview » (encore bloqué par le run réel).
