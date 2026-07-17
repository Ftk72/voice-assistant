# Mot d'éveil — provenance du code et des modèles vendorés

Tout ce dossier est **vendoré** : aucun CDN, aucune dépendance npm vivante,
aucun appel réseau à l'exécution (ADR 0007 — souveraineté ; ADR 0012 décision 2
— le mot d'éveil tourne dans la webview, l'audio ne quitte pas la machine).

Vendoré le **2026-07-17** (ticket wayfinder 0010), sources vérifiées par API
avant tout téléchargement, conformément au CLAUDE.md.

## Moteur — `moteur.js`

| | |
|---|---|
| Origine | npm `openwakeword-wasm-browser@0.1.1`, fichier `src/WakeWordEngine.js` |
| Amont | https://github.com/dnavarrom/openwakeword_wasm (portage web d'openWakeWord) |
| Licence | **MIT**, déclarée par le `package.json` du paquet npm |
| Modification | **une seule** : l'import `from 'onnxruntime-web'` → chemin relatif vers le runtime vendoré. Corps verbatim (403 lignes identiques à l'amont). |

**Réserve de licence à connaître** : le dépôt GitHub ne porte aucun fichier
LICENSE (`license: null` à l'API GitHub, vérifié le 2026-07-17). Seule la
métadonnée npm déclare MIT — c'est la publication npm qui vaut concession. D'où
le vendoring **depuis le tarball npm** et non depuis git : c'est la source dont
la licence est explicite. Usage personnel ici ; une revue formelle serait à
refaire avant tout usage commercial.

**Pourquoi vendoré et non en dépendance** (note de recherche 0009) : le portage
n'a qu'un mainteneur, 8 commits, aucune release taguée — fragile en dépendance
vivante. Internalisé, il ne fait que ~16 Ko de JS, maintenables par nous.

## Runtime ONNX — `ort/`

| | |
|---|---|
| Origine | npm `onnxruntime-web@1.27.0` (satisfait le `^1.23.2` requis par le portage) |
| Licence | MIT (Microsoft) |
| Fichiers | `ort.wasm.bundle.min.mjs` (point d'entrée ESM) + `ort-wasm-simd-threaded.mjs` (glue de chargement) + `ort-wasm-simd-threaded.wasm` (binaire) |

Les trois vont **ensemble** dans `ort/` : même le build « bundle » va chercher la
glue `.mjs` dynamiquement, qui charge à son tour le `.wasm` (constaté au run réel
2026-07-17 — le premier essai, sans la glue, échouait sur « Failed to fetch »).
`../eveil.js` pointe `ort.env.wasm.wasmPaths` sur ce dossier en chemin **absolu**
(`/eveil/ort/`) : un chemin relatif s'y redoublerait (voir le commentaire là-bas).

Variante **sans `jsep`** : pas de WebGPU, exécution CPU/WASM seule
(`executionProviders: ['wasm']`). Le binaire est dit « threaded » mais retombe
en **mono-thread** faute d'isolation cross-origin (COOP/COEP absents) — sans
conséquence sur des trames de 1280 échantillons.

## Modèles — `modeles/`

| | |
|---|---|
| Origine | release GitHub **`v0.5.1`** de https://github.com/dscripka/openWakeWord (assets) |
| Licence | Apache-2.0 (licence du dépôt openWakeWord) |

⚠️ **Piège évité** : la note de recherche 0009 indiquait de récupérer ces
modèles sur `huggingface.co/davidscripka/openwakeword`. **Ce dépôt HF est
vide** (`.gitattributes` + `README.md`, `usedStorage: 0`) et tagué
`cc-by-nc-sa-4.0`. La vraie source est la release GitHub ci-dessus. C'est la
récurrence du piège de `docs/impasses.md` (2026-07-02) : vérifier les noms de
fichiers par API avant toute commande de téléchargement. La note a été corrigée.

Les `.onnx` du tarball npm sont **byte-identiques** à ceux de la release v0.5.1
(sha256 comparés le 2026-07-17) : même provenance, licence Apache-2.0 retenue.

| Fichier | Taille | sha256 (32 premiers) | Rôle |
|---|---|---|---|
| `melspectrogram.onnx` | 1 087 958 o | `ba2b0e0f8b7b875369a2c89cb13360ff` | audio → mel-spectrogramme |
| `embedding_model.onnx` | 1 326 578 o | `70d164290c1d095d1d4ee149bc5e0054` | mel → embedding (96 dims) |
| `silero_vad.onnx` | 1 807 522 o | `a35ebf52fd3ce5f1469b2a36158dba76` | VAD — garde-fou : pas de détection hors parole |
| `hey_jarvis_v0.1.onnx` | 1 271 370 o | `94a13cfe60075b132f6a472e7e462e81` | **canari anglais** (voir ci-dessous) |

Empreintes du runtime : `ort.wasm.bundle.min.mjs` = `1db5e1c5cd2b860eed85e6eeff23e2aa`,
`ort-wasm-simd-threaded.wasm` = `d1ab1b94b16a65b29d710d0b587b29e7`.

## Le canari anglais, et la suite

`hey_jarvis` est un **modèle anglais** : ce n'est pas la destination, c'est le
canari. **Aucun modèle de mot d'éveil français n'existe** (recherche 0009, ni
côté openWakeWord ni côté sherpa-onnx) : le mot français doit être **entraîné
sur mesure** via le notebook Colab officiel d'openWakeWord (échantillons
positifs générés par Piper `fr_FR-upmc-medium`).

Le canari sert à prouver la chaîne — WASM sous WebView2, flux micro en veille,
détection → ouverture de conversation — **sans dépendre de cet entraînement**
(principe « un inconnu à la fois » de la carte wayfinder, le même qui a donné
« bouton d'abord »). Une fois le `.onnx` français entraîné, il se dépose ici et
`MOT_DEVEIL` change dans `../eveil.js` : rien d'autre ne bouge.

## Refaire ce vendoring

```sh
# Moteur + modèles (le tarball npm embarque les deux)
curl -sL -o owww.tgz https://registry.npmjs.org/openwakeword-wasm-browser/-/openwakeword-wasm-browser-0.1.1.tgz
# Runtime ONNX
curl -sL -o ort.tgz https://registry.npmjs.org/onnxruntime-web/-/onnxruntime-web-1.27.0.tgz
```

Les modèles se retrouvent aussi, à l'identique, en assets de
`https://github.com/dscripka/openWakeWord/releases/tag/v0.5.1`.
