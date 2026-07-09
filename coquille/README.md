# Coquille — application de bureau de l'assistant vocal

La **Coquille** (ADR 0010) est l'application de bureau **native Windows** de
l'assistant : elle est la carte son de la conversation (micro / haut-parleurs
via la webview) et assemble les fenêtres, l'icône de zone de notification et
les raccourcis. Elle ne contient **aucune logique métier** (ADR 0009 / 0010) :
le dialogue, le persona et la voix vivent dans les forges ; la coquille ne fait
qu'afficher et acheminer l'audio.

Bâtie sur **Tauri v2** (Rust + WebView2). Frontend statique HTML/CSS/JS
vanilla, sans bundler ni CDN (souveraineté, ADR 0007).

> **Aucun de ces fichiers n'a été compilé ni exécuté** dans l'environnement de
> développement (WSL2, sans cible Windows/WebView2 ni chaîne Rust ici). Le
> scaffold a été *grounder* sur la doc officielle Tauri v2 (URLs citées dans le
> code) mais la **vérification réelle est la manip Windows ci-dessous**, à la
> charge de l'utilisateur.

## Périmètre v1

- **Fenêtre « console »** (`console`) : héberge un **client voix** minimal
  (bouton « Parler »). Reprend la logique WebRTC du prototype du transport
  (getUserMedia + `RTCPeerConnection` + `POST /offer` + lecture de la piste de
  retour), **sans TURN ni relay** — coquille et transport sont co-localisés sur
  le même hôte Windows, la media passe en localhost.
- **Fenêtre « pastille »** (`pastille`) : petit indicateur flottant sans décor,
  toujours au-dessus, montrant les états veille / écoute / parle. **Stub
  visuel** en v1 (le clic fait défiler les états ; aucun branchement RTVI réel).
- **Tray** : icône de notification (clic gauche = afficher/masquer la console ;
  menu = console / pastille / quitter).
- **Raccourci global** : `Ctrl + Alt + Espace` affiche/masque la pastille.

Hors périmètre v1 (lots ultérieurs) : onglets de console chargeant les modules
des forges, notifications d'annonces, SDK Pipecat JS (le WebRTC brut suffit).

## Prérequis (sur Windows)

- **Rust** (toolchain MSVC) via `rustup` — <https://rustup.rs>.
- **Microsoft C++ Build Tools** (MSVC + Windows SDK).
- **WebView2 Runtime** : préinstallé sur Windows 11 et Windows 10 récents ;
  sinon « Evergreen WebView2 Runtime » de Microsoft.
- **Tauri CLI** (installée ci-dessous).

Doc officielle des prérequis : <https://v2.tauri.app/start/prerequisites/>

> ⚠️ **Gros téléchargements côté Windows** (plusieurs Go) : toolchain Rust,
> Build Tools MSVC, éventuellement le runtime WebView2, et la compilation des
> dépendances Tauri (première build longue). Ce sont des téléchargements
> Windows, hors du périmètre WSL2 — **à lancer par l'utilisateur**.

## Où lancer ces commandes (⚠️ Windows, pas WSL)

Ces commandes vont dans un **terminal Windows** (PowerShell ou cmd), **jamais
dans WSL** : `cargo` dans WSL construirait une app **Linux** (WebKitGTK), pas la
cible **WebView2** voulue.

Le code vit dans le système de fichiers WSL ; depuis Windows, `coquille/` est à
`\\wsl.localhost\Ubuntu-24.04\home\ftk\voice-assistant\coquille`. `cargo` sait
lire ce chemin UNC, mais l'I/O réseau est lent et le dossier de build sur FS
réseau pose problème — pointe la sortie de build sur un disque local Windows :

```powershell
$env:CARGO_TARGET_DIR = "C:\cargo-target\coquille"   # PowerShell
# set CARGO_TARGET_DIR=C:\cargo-target\coquille       # cmd
cd \\wsl.localhost\Ubuntu-24.04\home\ftk\voice-assistant\coquille
```

Installer Rust côté Windows (une fois) : `winget install Rustlang.Rustup` (ou
<https://rustup.rs>), puis `rustup default stable-msvc`.

## Commandes (à lancer SUR WINDOWS, depuis `coquille/`)

Réf. <https://v2.tauri.app/start/create-project/> et
<https://v2.tauri.app/reference/cli/>.

### 1. Installer la CLI Tauri (une fois)

```powershell
cargo install tauri-cli --version "^2.0.0" --locked
```

### 2. Générer les icônes (une fois — requis pour la build et le tray)

Fournir un logo carré (PNG, idéalement ≥ 1024×1024). La commande produit tout
le jeu d'icônes attendu par `tauri.conf.json` (dossier `src-tauri/icons/`) :

```powershell
cargo tauri icon chemin\vers\logo.png
```

### 3. Développer (fenêtres + rechargement)

```powershell
cargo tauri dev
```

Le frontend statique est servi directement depuis `src/`
(`build.frontendDist = "../src"`) : **aucun `npm`/`pnpm` ni serveur de dev**.

### 4. Compiler l'exécutable / l'installateur

```powershell
cargo tauri build
```

## Dépendance d'exécution : le transport voix

Le client voix appelle `http://127.0.0.1:8700/offer`. Le **transport voix**
(Pipecat) doit tourner en natif Windows sur ce port, transport `pipecat` activé
(`TRANSPORT_VOIX_TRANSPORT_BACKEND=pipecat`), sinon `/offer` répond `503`. Voir
`transport-voix/README.md`.

## Arborescence

```
coquille/
├── README.md
├── .gitignore
├── src/                     # Frontend statique (vanilla, zéro dépendance)
│   ├── index.html           # Console : client voix
│   ├── console.css
│   ├── console.js           # WebRTC vers le transport (sans TURN/relay)
│   ├── pastille.html        # Pastille : indicateur d'état (stub)
│   ├── pastille.css
│   └── pastille.js
└── src-tauri/               # Processus natif (Rust / Tauri v2)
    ├── Cargo.toml
    ├── build.rs
    ├── tauri.conf.json      # Fenêtres, CSP, bundle
    ├── src/
    │   ├── main.rs          # Point d'entrée → coquille_lib::run()
    │   └── lib.rs           # Fenêtres, tray, raccourci global
    ├── capabilities/
    │   └── default.json     # Permissions (cœur + raccourci global)
    └── icons/               # À GÉNÉRER (cargo tauri icon), non versionné vide
```

## Points de vigilance (non vérifiés ici)

- **Accès micro dans WebView2** : `getUserMedia` doit être autorisé par le
  moteur WebView2. À valider au premier `cargo tauri dev` ; si le micro est
  refusé, vérifier la gestion des permissions de périphérique WebView2 (piste à
  consigner dans `docs/impasses.md` le cas échéant).
- **Fenêtre transparente** (pastille) : le rendu de la transparence dépend de
  la plateforme ; à valider visuellement sur Windows.
- **Icônes** : sans `cargo tauri icon`, la build échoue (icônes référencées par
  `tauri.conf.json`) et le tray reste sans image (dégradé géré côté Rust).
- **Schéma des capabilities** (`gen/schemas/…`) : généré par `tauri-build` à la
  première compilation ; le `$schema` de `capabilities/default.json` n'est
  résolu qu'après.
