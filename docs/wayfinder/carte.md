---
label: wayfinder:map
cree: 2026-07-10
---

# Carte — Redémarrage clean : la stack qui parle

## Destination

Le dépôt est purgé du legacy OpenWebUI et réaligné (docs, compose), et
l'assistant **parle en réel sur Windows** : conversation ouverte au **mot
d'éveil français** ou à la pastille, multi-tours, interruption cohérente,
**capture mémoire validée** (obsolescence prouvée par l'expérience
« déménagement »), avec la **vraie voix** de l'utilisateur enrôlée — le tout
sanctionné par la recette ACCEPTANCE v2 rejouée.

Cadrage acté au grilling du 2026-07-10 : grand ménage **dans ce dépôt**
(historique conservé) ; on ne rebâtit **que le non-validé** (les forges
éprouvées restent telles quelles) ; la carte **porte l'exécution** (override
wayfinder « plan, don't do ») jusqu'à la stack qui parle.

## Notes

- **Exécution incluse** : les tickets `task` de cette carte livrent le travail,
  pas seulement la décision.
- Skills : `/impasses` avant tout diagnostic (le registre est riche et payé
  cher) ; `/premisses` en ouverture de chaque ticket ; `/delegate` pour les
  tickets AFK (jusqu'à **5 subagents en parallèle**) ; `/handoff` en fin de
  session.
- Téléchargements : les subagents sont autorisés jusqu'à **3 Go** (accord
  utilisateur du 2026-07-10, remplace le plafond 100 Mo du CLAUDE.md pour les
  tickets de cette carte) ; au-delà, commandes fournies à l'utilisateur.
- Constantes : tout en français ; jamais de `git commit` par l'agent ; TDD
  ports/adaptateurs (pattern memory-forge) ; RTX 5080 sm_120 = aucun binaire
  CUDA présumé compatible sans test réel ; `-j` borné sur toute compilation.
- Les tickets **HITL** exigent l'utilisateur au poste Windows (micro,
  navigateur, coquille) — l'agent ne peut pas les jouer seul.
- Séquencement hérité de l'ADR 0012 : **bouton d'abord** — le pont
  WebView2↔Pipecat se valide au bouton (un inconnu à la fois) avant
  d'empiler le mot d'éveil.

## Décisions jusqu'ici

<!-- une ligne par ticket clos : gist + lien -->

- [Ménage du dépôt](tickets/0001-menage-du-depot.md) — legacy purgé (openwebui,
  coturn, sans-stt, template Voxtral), compose v2 validé ; orphelins à stopper
  via `--remove-orphans` après la session de test.
- [La voix du flux appliquée par tour](tickets/0004-voix-du-flux-appliquee-par-tour.md)
  — `TTSUpdateSettingsFrame` avant chaque phrase au changement de voix ;
  16 tests verts ; confirmation en réel différée (2e voix requise).
- [Expérience déménagement](tickets/0006-experience-demenagement.md) — **OUI**,
  l'obsolescence Graphiti tient en réel (Paris `invalid_at` à l'instant du
  `/clore` Lyon, invalidation transitive comprise) ; image `memory` périmée à
  rebuilder.

- [Recherche mot d'éveil français](tickets/0009-recherche-mot-d-eveil-francais.md) — openWakeWord + portage WASM vendoré, mot FR à entraîner sur mesure (aucun modèle prêt) ; Porcupine disqualifié (AccessKey réseau) ; plan B : bouton.

## Pas encore spécifié

- **Ce que le run réel révélera** : sample_rate réel de voice-forge vs
  pipeline, comportement getUserMedia/WebView2, événements RTVI réels — des
  correctifs naîtront du ticket « Run réel bout-en-bout sur Windows », de
  nature inconnaissable avant.
- **Presets audio casque / haut-parleurs** : si le run réel sur haut-parleurs
  produit de fausses interruptions (AEC insuffisante), la bascule preset
  (glossaire) se ticketera — côté coquille + transport.
- **Arbitrage latence** : si la voix→voix mesurée dépasse la cible ≤ 2 s
  (mur connu : TTS non streamé 1,72 s sur l'ancienne stack), décider quoi
  relâcher — la cible, ou engager le TTS streamé (dont l'exécution est hors
  carte, chantier C2).
- **Contrat voix par défaut / voix d'annonce** au-delà de l'enrôlement
  (reste du lot B2) : qui détient la voix par défaut système, comment elle se
  change depuis `/admin`.
- **Sort des mesures de référence** de l'ancienne stack (2,88 s voix→voix…)
  dans ACCEPTANCE v2 : références historiques ou critères réactualisés.

## Hors périmètre

- **C1 proactivité, C2 Qwen3-TTS / TTS streamé, C3 identification du
  locuteur, C4 vision d'écran** — la roadmap « Ensuite » reprend après la
  destination.
- **Lots UI de confort** : tranches B1 restantes (curseur temporel, recherche
  d'entité, bascule 2D/3D), B4 notifications d'annonces dans la pastille —
  utiles, mais la stack parle sans eux.
- Domotique, RAG-upload-en-chat — déjà hors roadmap (grilling 2026-07-07,
  ADR 0009).
