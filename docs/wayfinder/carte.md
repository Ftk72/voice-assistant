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
- [RTVI réel dans la pastille](tickets/0007-rtvi-reel-dans-la-pastille.md) —
  pastille pilotée par les événements RTVI (console lit le canal, relaie l'état
  veille/écoute/parle par événement Tauri) ; **validé au réel le 2026-07-16**.
  Débloque 0008 (module dialogue).
- [Run réel bout-en-bout](tickets/0003-run-reel-bout-en-bout.md) — la stack
  **parle** au poste Windows (bouton → STT FR → Dialogue Forge → TTS → audio) ;
  pièges levés (CORS, VAD 1.5, WAV float32, timeout httpx) ; STT TTFB 0,3-0,5 s.
  Latence voix→voix en régime **restant à mesurer** (0011). Le grand débloqueur.
- [Module dialogue (A4)](tickets/0008-module-dialogue-a4.md) — la conversation se
  **suit depuis la console** : page servie par le DF en iframe, fil au timing de
  synthèse, menus persona/voix pilotant la conversation **live**, indicateur
  d'outils ; **validé au réel le 2026-07-17**. A exigé un canal de commande
  bidirectionnel (page et transport tenaient deux conversations DF distinctes —
  les menus ne commandaient rien). Reste : liste complète des voix enrôlées
  (accès cross-forge à voice-forge, à cadrer).
- [Mot d'éveil dans la webview](tickets/0010-mot-d-eveil-dans-la-webview.md) —
  « hey Jarvis » (canari anglais openWakeWord WASM, vendoré zéro-CDN) **ouvre une
  conversation depuis la veille** ; **validé au réel le 2026-07-17** (WASM sous
  WebView2, détection 0.96, reprise de veille si transport injoignable). Détection
  dans `console.js` (événement d'entrée, pas la pastille — enquête sourcée). Reste
  hors périmètre : entraîner le **mot français** (canari anglais en attendant),
  régler les faux positifs, et un éventuel mot d'arrêt parlé (à arbitrer).
- [Docs racine v2](tickets/0002-docs-racine-v2.md) — documentation racine
  réalignée ADR 0009 (README, ACCEPTANCE v2 = spec de 0011, plan de tests,
  CLAUDE.md) ; OpenWebUI purgé des docs vivantes ; mesures anciennes gardées en
  repères, cibles v2 en relatif (≤ 2 s).
- [Atelier d'enrôlement de la vraie voix](tickets/0005-enrolement-de-la-vraie-voix.md)
  — les deux voies validées au réel le 2026-07-17 : dépôt multi-format (décodage
  **ffmpeg** en sous-processus, décision tranchée) et capture micro navigateur
  (WebM/Opus → `decodeAudioData` → WAV PCM16).
- [Clonage réel de la voix](tickets/0012-clonage-reel-de-la-voix.md) — la
  prémisse était fausse : Chatterbox + torch 2.8/cu128 déjà en place, sm_120
  franchi ; **clone français audible et propre** validé à l'oreille le
  2026-07-17 (1,75 s en régime, pas de pagination LLM).
- [Liste complète des voix enrôlées](tickets/0013-liste-complete-des-voix-enrolees.md)
  — contrat cross-forge : **le Dialogue Forge proxie voice-forge** (`GET /voix`),
  détail du contrat dans le ticket.
- [Réglage grand public voix + persona](tickets/0014-reglage-grand-public-voix-persona.md)
  — variante B (formulaire) retenue, **préférence permanente persistée** côté DF ;
  onglet Réglages de la coquille validé au réel le 2026-07-18 (persona
  assistant et voix Jackie).
- [Bascule des consommateurs sur la vraie voix](tickets/0015-bascule-consommateurs-vraie-voix.md)
  — **voix par défaut système : Jackie** (choix utilisateur) sur les trois
  consommateurs (annonces time-forge, `tts_voix_defaut` du transport, persona
  assistant) ; annonce enceintes validée à l'oreille le 2026-07-18.

## Pas encore spécifié

<!-- Nettoyage du 2026-07-18 : les nappes levées par 0002/0003/0005/0012/0014/0015
     sont sorties d'ici — « Qualité du clone à l'oreille » a gradué en ticket 0023,
     « formats acceptés » est tranché par le décodage ffmpeg (0005), « contrat voix
     par défaut » par 0014+0015, « sort des mesures » par 0002, et les correctifs
     du run réel sont nés puis absorbés (0003, 0007, 0008, 0010). -->

- **Presets audio casque / haut-parleurs** : si la recette (0011) sur
  haut-parleurs produit de fausses interruptions (AEC insuffisante), la bascule
  preset (glossaire) se ticketera — côté coquille + transport.
- **Montée Chatterbox V3** (grilling fidélité du 2026-07-18) : l'amont annonce
  une similarité locuteur et une stabilité meilleures — gros téléchargement
  (lancé par l'utilisateur) et compatibilité torch 2.8/sm_120 à requalifier.
  Ne se tickete que si l'escalade douce du ticket
  [Qualité du clone à l'oreille](tickets/0023-qualite-du-clone-a-l-oreille.md)
  (échantillon soigné + réglages par voix) laisse le verdict d'oreille
  insuffisant.
- **Arbitrage latence** : si la voix→voix mesurée en 0011 dépasse la cible ≤ 2 s
  (mur connu : TTS non streamé 1,72 s sur l'ancienne stack), décider quoi
  relâcher — la cible, ou engager le TTS streamé (dont l'exécution est hors
  carte, chantier C2).

## Hors périmètre

- **Limite de taille du dépôt de voix** (reliquat de la nappe « formats &
  limite » levée par 0005) : les formats sont tranchés (tout ce que ffmpeg
  décode, sinon 415) ; borner la taille des fichiers déposés est du
  durcissement qui ne conditionne pas la destination — app locale, mono-
  utilisateur.
- **Changement de la voix d'annonce depuis une UI** : la voix par défaut
  système vit dans compose/config (décidé en
  [Bascule des consommateurs sur la vraie voix](tickets/0015-bascule-consommateurs-vraie-voix.md)),
  le réglage utilisateur passe par l'onglet Réglages (0014) ; une UI dédiée à
  la voix d'annonce est du confort au-delà de la destination.
- **C1 proactivité, C2 Qwen3-TTS / TTS streamé, C3 identification du
  locuteur, C4 vision d'écran** — la roadmap « Ensuite » reprend après la
  destination.
- **Lots UI de confort** : tranches B1 restantes (curseur temporel, recherche
  d'entité, bascule 2D/3D), B4 notifications d'annonces dans la pastille —
  utiles, mais la stack parle sans eux.
- Domotique, RAG-upload-en-chat — déjà hors roadmap (grilling 2026-07-07,
  ADR 0009).
