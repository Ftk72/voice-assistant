# Recherche — mot d'éveil français dans la webview (WebView2)

Date : 2026-07-16 · Statut : recherche documentaire (aucun test micro possible en
WSL2 — cf. brief) · Répond au ticket wayfinder « Recherche mot d'éveil
français », différée par l'ADR 0012 décision 2 (le mot d'éveil tournera **dans
la webview de la coquille**, pas côté serveur).

## Contexte rappelé

ADR 0012 §Décisions, point 2 : « Quand le mot d'éveil sera ajouté, il tournera
**dans le navigateur** (l'audio ne quitte pas la webview en veille ; "rien ne
quitte la machine" poussé au processus), pas côté serveur. » La coquille est
Tauri v2 + WebView2 (Chromium sous Windows), frontend vanilla sans bundler ni
CDN : toute dépendance doit être vendorée en fichiers statiques (JS/WASM/ONNX)
dans le dépôt.

Contrainte transversale (ADR 0007, souveraineté) : aucune requête réseau
après déploiement, aucun compte/clé nécessitant une validation en ligne.

## Tableau comparatif

| Candidat | Licence | Taille à vendorer | Français | Hors-ligne prouvé | Voie WebView2 | Maturité | Qualité rapportée |
|---|---|---|---|---|---|---|---|
| **openWakeWord** (moteur) + **openwakeword_wasm** (portage web) | openWakeWord : Apache-2.0. Portage `dnavarrom/openwakeword_wasm` : MIT (déclaré dans `package.json` npm, aucun fichier LICENSE au dépôt — à vérifier avant usage commercial mais compatible ici) | ~19 Mo (`openwakeword-wasm-browser@0.1.1` sur npm, poids décompressés) : melspectrogram.onnx, embedding_model.onnx, silero_vad.onnx, un `.onnx` par mot-clé (~1-2 Mo chacun), wasm d'onnxruntime-web | **Aucun modèle FR officiel ni communautaire prêt à l'emploi** trouvé (bibliothèque communautaire = modèles anglais : hey_jarvis, alexa, hey_mycroft, timer, weather…). Un mot FR s'obtient par **entraînement custom** (voir plus bas) | Oui — pipeline 100 % local une fois les poids chargés (aucun appel réseau après chargement) | **Oui, portage éprouvé** : `dnavarrom/openwakeword_wasm` (GitHub, 6★ certes modeste, dernier commit 2025-11-23) expose une classe `WakeWordEngine` (`load()/start()/stop()/setActiveKeywords()`, événement `detect`) au-dessus d'`onnxruntime-web`, pipeline complet mel→embedding→classifieur en WASM. Existe aussi une démo indépendante (deepcorelabs.com) qui confirme la faisabilité WASM/WebGPU | openWakeWord (moteur) : mûr, 2534★, dernier commit 2025-12-30, 123 issues ouvertes — actif. Le portage web (`openwakeword_wasm`) : très jeune (8 commits, 1 mainteneur, 6★, aucune release taguée, pas de tests visibles) — **fragile, à traiter comme un patch à internaliser, pas une dépendance stable** | Moteur Python original : bien documenté sur faux positifs/négatifs en environnement ouvert (bruit ambiant, TV) via le repo dscripka. Portage WASM : pas de retours d'usage réel trouvés (projet trop récent) |
| **sherpa-onnx (k2-fsa)** — keyword spotting | Apache-2.0 (dépôt entier, y compris WASM et modèles officiels) | Modèle KWS zipformer : quelques dizaines de Mo (comparable aux modèles ASR streaming, ~60-70 Mo pour les zipformer légers) + `sherpa-onnx-wasm-main-kws.js`/`.wasm` (runtime commun aux démos wasm du projet, plusieurs Mo) | **Aucun modèle KWS français officiel.** Les 3 modèles KWS publiés sont : `sherpa-onnx-kws-zipformer-zh-en-3M` (zh+en), `sherpa-onnx-kws-zipformer-wenetspeech-3.3M` (zh), `sherpa-onnx-kws-zipformer-gigaspeech-3.3M` (en). Le système est **« open vocabulary »** (un mot-clé arbitraire s'encode en tokens via `sherpa-onnx-cli text2token`, sans réentraînement) — mais les tokens BPE viennent du vocabulaire d'entraînement (anglais ou chinois) : un mot français fonctionnerait en approximation phonétique **dégradée**, jamais testé/documenté pour le FR | Oui, hors ligne par conception (le README du projet le revendique explicitement : « without Internet connection ») | **Oui, démo officielle** : `wasm/kws/` dans le dépôt (`app.js`, `sherpa-onnx-kws.js`, `sherpa-onnx-wasm-main-kws.cc`, build via `build-wasm-simd-kws.sh`) — c'est un artefact **officiel et maintenu**, contrairement au portage openWakeWord | Très mûr et très actif : 13 600★, dernier push **2026-07-15** (veille de cette recherche), mainteneurs k2-fsa (équipe Next-gen Kaldi, sérieuse, nombreux projets ASR/TTS reconnus) | Bonne réputation générale du moteur KWS en zh/en ; **aucune donnée sur le FR** puisqu'aucun modèle FR n'existe — le risque qualité est entièrement sur l'approximation phonétique d'un mot français avec un tokenizer anglais |
| **Porcupine (Picovoice)** | SDK on-device open-source, mais **modèles et moteur d'inférence propriétaires** ; usage soumis aux conditions Picovoice (gratuit avec limites, payant au-delà) | Petit : `.ppn` (quelques centaines de Ko) + `porcupine-web` (wasm) quelques Mo | **Oui, natif et officiel** — français dans la liste des langues supportées (avec en, de, it, ja, ko, pt, es, zh) | **Non — rédhibitoire.** Depuis la v2, l'AccessKey doit être **validée périodiquement par contact au serveur Picovoice** (activation + reporting de consommation pour la facturation) ; le traitement audio est local mais le moteur « appelle à la maison » pour rester actif. Confirmé par la discussion Hacker News et par le principe même du modèle freemium/AccessKey Picovoice | Oui, `@picovoice/porcupine-web` est un package npm officiel avec quickstart documenté | Très mûr et professionnel (produit commercial soutenu) | Réputation d'excellente précision (produit commercial optimisé), mais **disqualifié par la contrainte de souveraineté** avant même d'évaluer la qualité |
| Vosk KWS / micro-modèles dédiés | — | — | — | — | Aucune voie WASM/navigateur crédible et maintenue trouvée pour du KWS dédié (Vosk expose surtout de l'ASR complète, lourde pour un mot d'éveil low-power) | — | Écarté faute de piste sérieuse dans le temps imparti |

## Recommandation

**Retenir openWakeWord + le portage `openwakeword_wasm`, avec un mot d'éveil
français entraîné sur mesure**, plutôt que sherpa-onnx.

Raisonnement :
- sherpa-onnx a une **voie WASM plus solide et mieux maintenue** (démo
  officielle, dépôt Apache-2.0 très actif), mais **aucun modèle KWS français
  n'existe** et l'« open vocabulary » BPE n'est validé qu'en zh/en — utiliser
  un mot français dessus est une expérimentation non documentée, avec un
  risque qualité inconnu et pas de garde-fou (pas de retours d'autres
  utilisateurs à consulter en cas de problème).
- openWakeWord a un **chemin d'entraînement français balisé et déjà pratiqué
  par la communauté** (guide Home Assistant, Piper TTS voix `fr_FR-upmc-medium`,
  notebook Colab officiel `training_models.ipynb`) : on maîtrise ce qu'on
  entraîne, on peut ajuster `false_activation_penalty` en connaissance de
  cause (retours d'utilisateurs réels sur ce paramètre), et le moteur Python
  d'origine a une réputation établie sur les faux positifs/négatifs en
  conditions réelles (bruit, TV).
- Le seul défaut d'openWakeWord est **le portage web** (`openwakeword_wasm`,
  8 commits, 1 mainteneur, aucune release taguée) : jeune et fragile. Le
  contournement : **vendorer ce portage comme du code interne** (copier les
  fichiers dans le dépôt, pas de dépendance npm vivante), l'auditer avant
  intégration (licence MIT confirmée, ~19 Mo décompressés), et prévoir de le
  maintenir soi-même si le projet amont s'arrête — c'est un risque gérable,
  pas un risque bloquant.

### Voie d'intégration précise

1. **Entraînement** (une fois, hors du budget « pas de gros téléchargement
   sans accord ») : notebook officiel
   `github.com/dscripka/openWakeWord/blob/main/notebooks/training_models.ipynb`
   sur Colab gratuit, échantillons positifs générés par Piper TTS
   (`fr_FR-upmc-medium`, éventuellement complétés par le TTS local voice-forge
   `VoixDeTest` pour varier le timbre) + négatifs (bruit, parole française
   générique). Sortie : un `.onnx` par mot-clé retenu.
2. **Vendorer dans le dépôt** (`coquille/` — ADR 0009, module d'interface) :
   > **CORRECTION 2026-07-17 (intégration, ticket 0010)** : la source HF
   > indiquée ci-dessous est **fausse** — `huggingface.co/davidscripka/openwakeword`
   > est **vide** (`.gitattributes` + `README.md`, `usedStorage: 0`, tagué
   > `cc-by-nc-sa-4.0`). C'est la récurrence exacte de l'impasse 2026-07-02. La
   > vraie source des modèles partagés est la **release GitHub `v0.5.1`** de
   > `dscripka/openWakeWord` (Apache-2.0), qui les porte en assets — ou, plus
   > simple, le **tarball npm `openwakeword-wasm-browser@0.1.1`** qui embarque à
   > la fois le moteur ET les modèles (byte-identiques à la release, sha256
   > vérifiés). Détail dans `coquille/src/eveil/PROVENANCE.md`.
   - `melspectrogram.onnx`, `embedding_model.onnx` (partagés, fournis par
     openWakeWord — ~~à récupérer sur `huggingface.co/davidscripka/openwakeword`~~,
     cf. correction ci-dessus, `docs/impasses.md` 2026-07-02) ;
   - `silero_vad.onnx` (VAD, même source) ;
   - le `.onnx` du mot d'éveil français entraîné à l'étape 1 ;
   - les fichiers wasm/js d'`onnxruntime-web` (récupérables depuis le paquet
     npm `onnxruntime-web`, à copier statiquement — pas de CDN) ;
   - le wrapper `openwakeword_wasm` (copier son code source, pas `npm install`
     en dépendance vivante vu sa jeunesse — l'internaliser sous
     `coquille/src/wakeword/` avec attribution de licence MIT en commentaire).
3. **API JS** : `WakeWordEngine.load({modelPaths...})`, puis `start()` sur le
   flux `getUserMedia` déjà utilisé pour Pipecat (ADR 0010), écoute de
   l'événement `detect` pour déclencher l'ouverture de conversation (même
   point d'entrée que le bouton pastille, ADR 0012 décision 1).
4. **Validation avant bascule** : mesurer faux positifs/négatifs *in situ*
   (pièce, distance, TV allumée) — l'utilisateur teste, WSL2 n'a pas de micro.

### Plan B

Si le mot français entraîné maison se révèle de mauvaise qualité (trop de
faux positifs/négatifs) : **rester en mode bouton-poussoir** (ADR 0012
décision 1, déjà la V1 actée) plus longtemps, et réévaluer sherpa-onnx quand
(si) un modèle KWS multilingue ou francophone officiel apparaît — le dépôt
est assez actif (push quotidien observé) pour que ça arrive. Ne pas se
rabattre sur Porcupine : la validation réseau périodique de l'AccessKey
contredit directement ADR 0007 (aucune requête sortante hors recherche
documentaire anonyme) et le principe « rien ne quitte la machine » de l'ADR
0012 lui-même.

## Risques ouverts (pour arbitrage utilisateur, pas décision prise ici)

- **Aucune voie navigateur n'est un produit fini et stable** pour du wake
  word français : la recommandation combine un moteur mûr (openWakeWord) et
  un portage web jeune à un seul mainteneur (`openwakeword_wasm`) — c'est un
  pari raisonnable mais pas une dépendance « boring » au sens du reste de la
  stack (whisper.cpp, llama.cpp). Si l'équipe préfère du 100 % maintenu,
  sherpa-onnx WASM est plus solide *mais sans mot français* — il faudrait
  soit accepter la dégradation phonétique du mot-clé en BPE anglais/chinois,
  soit attendre un modèle KWS francophone officiel côté k2-fsa.
- Le portage `openwakeword_wasm` n'ayant pas de LICENSE file au dépôt (seule
  la métadonnée npm `package.json` déclare MIT), vérifier ce point avant de
  vendorer si une revue de licence formelle est requise.
- Aucun test réel n'a été conduit dans cette recherche (contrainte WSL2 sans
  micro, cf. brief) — la qualité du mot d'éveil français entraîné maison
  reste **à valider en conditions réelles par l'utilisateur** avant toute
  bascule hors du mode bouton.
- Ce choix ne révise pas l'ADR 0012 : il documente juste *comment* honorer sa
  décision 2 quand le lot mot d'éveil sera lancé ; la décision de lancer ce
  lot (et le budget d'entraînement/temps associé) appartient à l'utilisateur.

## Sources (URLs primaires, consultées 2026-07-16)

- ADR 0012 : `docs/adr/0012-transport-voix-cycle-conversation-interruption-contrat-df.md` (dépôt local)
- openWakeWord (moteur) — dépôt : https://github.com/dscripka/openWakeWord
  (Apache-2.0, `pushed_at` API GitHub = 2025-12-30, 2534★, 123 issues ouvertes)
- Modèles pré-entraînés officiels : https://huggingface.co/davidscripka/openwakeword
  (vérifier les noms de fichiers exacts via `https://huggingface.co/api/models/davidscripka/openwakeword`
  avant toute commande de téléchargement, conformément à la leçon impasses 2026-07-02)
- Bibliothèque communautaire de mots d'éveil : https://openwakeword.com/library
  (aucun mot français prêt à l'emploi trouvé lors de cette recherche — à
  reconsulter, la bibliothèque évolue)
- Notebook d'entraînement officiel : https://github.com/dscripka/openWakeWord/blob/main/notebooks/training_models.ipynb
- Guide communautaire de mot d'éveil français (Home Assistant) : https://community.home-assistant.io/t/guide-train-a-custom-french-wake-word-for-home-assistant-with-openwakeword-colab/943111
  (Piper TTS `fr_FR-upmc-medium`, Colab gratuit, export ONNX→TFLite, retours
  utilisateurs sur `false_activation_penalty`)
- Portage WASM openWakeWord : https://github.com/dnavarrom/openwakeword_wasm
  (MIT via `package.json` npm, `pushed_at` API GitHub = 2025-11-23, 8 commits,
  6★, classe `WakeWordEngine`) — paquet npm miroir :
  https://www.npmjs.com/package/openwakeword-wasm-browser
  (`npm view` via registry API : licence MIT, version 0.1.1, ~19 Mo décompressés,
  publié 2025-11-23)
- Démo indépendante confirmant la faisabilité WASM/WebGPU : https://deepcorelabs.com/open-wake-word-on-the-web/
- sherpa-onnx (k2-fsa) — dépôt : https://github.com/k2-fsa/sherpa-onnx
  (Apache-2.0, `pushed_at` API GitHub = 2026-07-15, 13 600★)
- Documentation keyword spotting sherpa-onnx : https://k2-fsa.github.io/sherpa/onnx/kws/index.html
  (liste des 3 modèles KWS officiels, tous zh et/ou en ; principe « open
  vocabulary » via `sherpa-onnx-cli text2token`)
- Démo WASM KWS officielle : https://github.com/k2-fsa/sherpa-onnx/tree/master/wasm/kws
  et script de build : https://github.com/k2-fsa/sherpa-onnx/blob/master/build-wasm-simd-kws.sh
- Porcupine — introduction et quickstart web : https://picovoice.ai/docs/porcupine/
  et https://picovoice.ai/docs/quick-start/porcupine-web/
- FAQ Picovoice (nature open-source des SDK vs modèles propriétaires) : https://picovoice.ai/docs/faq/general/
- Discussion communautaire sur la nécessité de contact réseau périodique de
  l'AccessKey (v2+) : https://news.ycombinator.com/item?id=33964527

## Écarts par rapport au brief

- Aucun test réel (génération d'échantillons via voice-forge + mesure
  openWakeWord en WSL) n'a été conduit : la recherche documentaire a suffi à
  trancher clairement (aucun modèle FR n'existe côté ni openWakeWord ni
  sherpa-onnx, donc un test local n'aurait mesuré qu'un modèle anglais ou un
  entraînement custom hors budget de cette session) — jugé conforme à
  l'arbitrage proposé par le brief (« une recherche solidement sourcée sans
  test vaut mieux qu'un test bâclé »).
- Vosk KWS et « micro-modèles dédiés » n'ont reçu qu'une recherche rapide,
  faute de piste crédible trouvée dans le temps imparti ; à ne pas prendre
  comme une revue exhaustive de cette famille si le sujet redevient chaud.
