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

## Avancement (session 2026-07-17) — chaîne câblée, canari anglais

Séquencement retenu (accord utilisateur) : **canari anglais d'abord**. Toute la
chaîne détection → ouverture est câblée et vendorée avec `hey_jarvis` (modèle
anglais existant) pour la prouver sous WebView2 **sans dépendre** de
l'entraînement du mot français (principe « un inconnu à la fois »). Le mot
français s'y substituera par simple dépose d'un `.onnx` + 2 constantes.

**Emplacement tranché (enquête sourcée, corrige la lettre du ticket)** : la
détection va dans **`console.js`**, pas dans la pastille. Raison : `lib.rs`
*masque* les fenêtres, ne les ferme jamais (`hide()`, jamais `close()`) — les
deux survivent également en veille ; la console détient déjà le micro, le bouton
et l'ouverture de conversation, la pastille n'a ni micro ni connexion. Détecter
un mot d'éveil est un **événement d'entrée** (même classe qu'un clic bouton), pas
une décision métier — ADR 0009 tenu. La formule « webview de la pastille » date
d'avant la séparation console/pastille ; l'intention ADR 0012 est « dans la
webview, pas côté serveur », ce que la console satisfait.

**Livré (jamais exécuté — se prouve au run réel WebView2)** :

- **Vendoring** sous `coquille/src/eveil/` (~18,5 Mo, zéro CDN, zéro réseau —
  ADR 0007) : moteur openWakeWord (`moteur.js`, 16 Ko, verbatim au portage npm à
  l'import près), runtime `onnxruntime-web@1.27.0` (build ESM wasm-only + binaire
  SIMD), 4 modèles (`melspectrogram`, `embedding_model`, `silero_vad`,
  `hey_jarvis_v0.1`). Provenance + sha256 + réserve de licence dans
  `eveil/PROVENANCE.md`. Sources vérifiées par API avant tout téléchargement.
- **Câblage** (`coquille/src/eveil.js`, notre code, français) : `WakeWordEngine`
  chargé au démarrage, écoute en veille ; `detect` → `window.coquilleEveil.ouvrir()`
  = le point d'entrée exact du bouton (le mot d'éveil OUVRE, ne re-filtre pas les
  tours, ADR 0012 déc. 1). Cohabitation des micros : la veille tient son propre
  `getUserMedia` 16 kHz, rendu le temps d'une conversation
  (`conversation-ouverte`/`-fermee`), repris au raccrochage.
- **`console.js`** : point d'entrée `window.coquilleEveil` exposé ; transitions
  de conversation annoncées ; **fuite de micro corrigée** (`raccrocher()` ne
  coupait pas les pistes `getUserMedia` — bloquant pour la reprise de veille) ;
  chemin `abandonner()` qui rend le micro et rouvre la veille sur tout échec de
  connexion survenu micro déjà pris.
- **CSP** (`tauri.conf.json`) : `script-src 'self' 'wasm-unsafe-eval' blob:` —
  sans quoi WebView2 refuse WASM et l'AudioWorklet Blob **en silence** (registre
  d'impasses 2026-07-17, même classe que le `frame-src` du ticket 0008).
- **Docs** : note de recherche 0009 corrigée (source HF fausse) ; 2 pièges au
  registre d'impasses (CSP silencieuse, dépôt HF vide).

**Robustesse** : l'échec de chargement du moteur est sans conséquence — le
bouton reste le chemin nominal (plan B du ticket, déjà acté).

### Reste à faire

- **HITL au poste Windows** : lancer la coquille, vérifier que « hey Jarvis »
  ouvre une conversation depuis la veille (pastille veille → écoute), mesurer les
  faux positifs (télé, musique, distance de pièce). Bloc `/newbie` fourni en
  session.
- **À prouver au run réel** (inconnus WebView2, non levables en WSL) :
  1. WebView2 compile bien le WASM sous la CSP élargie ;
  2. une **fenêtre Tauri masquée** ne suspend pas la détection (Chromium peut
     geler une page cachée ; la capture micro active protège *normalement*, mais
     non documenté pour WebView2 fenêtre masquée) ;
  3. la cohabitation des deux `getUserMedia` (veille 16 kHz + conversation) et
     l'AEC ne se gênent pas au basculement.
- **Entraînement du mot français** (session Colab, côté utilisateur) : notebook
  officiel openWakeWord, positifs Piper `fr_FR-upmc-medium` ; le `.onnx` obtenu
  se dépose dans `eveil/modeles/`, `MOT_DEVEIL`/`FICHIER_MODELE` changent dans
  `eveil.js`. Le canari valide tout le reste d'ici là.
- **Ne pas clore** avant la validation HITL du critère (« dis… » ouvre en réel).
