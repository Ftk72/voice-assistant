# Host Bridge (Pont hôte)

Le pied de l'assistant **sur la machine hôte, hors Docker** (phase 4, ADR 0008).
Deux rôles, aucune intelligence :

- **Enceintes** — reçoit un wav déjà synthétisé (par le Time Forge via le Voice
  Forge) et le joue sur les haut-parleurs : c'est ainsi que passent les annonces.
- **Catalogue d'actions** — exécute les actions de la liste blanche `catalog.toml`
  (ouvrir une application, piloter la musique, régler le volume…). **Jamais** de
  commande arbitraire (CONTEXT.md § Actions).

## Pourquoi hors Docker

Les conteneurs n'ont ni les enceintes ni le bureau de l'hôte : ils ne peuvent ni
faire du son sur les haut-parleurs, ni ouvrir une application (surtout sous WSL).
Le Pont est le seul composant qui tourne sur l'hôte pour donner ce pied — un seul
à installer et maintenir (ADR 0008).

## Lancement (sur l'hôte)

```bash
uv sync
cp catalog.example.toml catalog.toml   # puis décrivez VOS actions
uv run python -m app
```

Joignable depuis les conteneurs via `http://host.docker.internal:8500` (le Time
Forge y envoie ses annonces ; OpenWebUI y branche le serveur MCP
`http://host.docker.internal:8500/mcp`).

## Sécurité

- En usage réel, écouter sur `0.0.0.0` (`HOST_BRIDGE_HOST=0.0.0.0`) pour être
  joignable depuis le réseau Docker, et **limiter au réseau Docker par le
  pare-feu**. Le Pont n'expose que la liste blanche du catalogue, jamais un shell.
- **Jeton partagé** : `0.0.0.0` expose aussi le Pont au LAN (surtout si WSL passe
  en réseau « mirrored »). Définir `HOST_BRIDGE_TOKEN` au lancement du Pont
  (même valeur que `HOST_BRIDGE_TOKEN` du `.env` racine, que le compose passe au
  Time Forge) : toute requête doit alors porter le header `X-Bridge-Token`, sauf
  `/health`. Jeton vide = auth désactivée (dev local sur 127.0.0.1 uniquement).
- Le catalogue est fermé : ce qui n'y figure pas ne peut pas être lancé, point.

## Adaptateurs

Ports/adaptateurs : les factices (défaut) servent aux tests et au dev, sans
toucher au bureau ni aux enceintes.

- Runner : `fake` (défaut, garde trace) · `subprocess` (`HOST_BRIDGE_RUNNER=subprocess`,
  `Popen` d'un argv explicite, jamais `shell=True`).
- Player : `fake` (défaut) · `auto` (`HOST_BRIDGE_PLAYER=auto`, `winsound` sous
  Windows, `aplay` sous Linux).

`SystemPlayer` (branche Linux/aplay, WSLg → enceintes Windows) est **validé en
réel le 2026-07-07** (chaîne Voice Forge → `/play` → enceintes). Prérequis dans
WSL, installés une fois à la main : `pulseaudio-utils alsa-utils
libasound2-plugins` et un `/etc/asound.conf` routant ALSA vers Pulse
(`pcm.!default { type pulse }`). Le lancement au boot est assuré par
`scripts/demarrage-hote.sh`. `SubprocessRunner` reste **jamais exécuté à ce
jour** (pattern GraphitiMemory) : à valider au premier usage d'une action du
catalogue.

## Dev

```bash
uv run pytest
uv run ruff check .
```
