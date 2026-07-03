# ADR 0008 — Le Pont hôte : un seul pied hors Docker

Date : 2026-07-02 · Statut : accepté

## Contexte

Deux capacités du quotidien ne peuvent pas vivre dans un conteneur. L'**Annonceur**
(phase 3) doit faire entendre une annonce sur les **enceintes** de la machine, sans
conversation en cours. Le **Catalogue d'actions** (phase 4) doit **agir sur le
bureau** de l'hôte — ouvrir une application, piloter la musique, régler le volume.
La cible réelle est un poste Windows (avec WSL) ; le développement se fait sous
Linux. Or les conteneurs Docker n'ont ni les enceintes ni le bureau de l'hôte :
ils ne peuvent faire ni l'un ni l'autre, en particulier sous WSL.

## Décision

Un **seul** composant tourne hors Docker : le **Pont hôte** (`host-bridge/`).

- FastAPI minimal, joignable depuis les conteneurs via `host.docker.internal:8500`.
- **Sans intelligence** : il ne décide rien.
  - Enceintes : il **reçoit du wav prêt à jouer** et le joue. La synthèse reste
    dans le Time Forge, qui passe par le Voice Forge (mêmes voix que l'assistant).
  - Actions : il n'exécute **que la liste blanche** de `catalog.toml` (argv
    explicite par plateforme, jamais un shell), jamais une commande arbitraire.
- Les conteneurs le joignent grâce à `extra_hosts: host.docker.internal:host-gateway`
  (service `time` du docker-compose).

## Justification

- **Un seul pied sur l'hôte** à installer et maintenir, plutôt que plusieurs agents.
- **Le TTS reste centralisé** dans le Voice Forge : l'annonce a la même voix que
  l'assistant, et la pile voix n'est pas dupliquée sur l'hôte.
- **La liste blanche borne le risque** : la fiabilité d'appel d'outils d'un LLM
  35B local n'est pas validée ; un catalogue fermé garantit que rien d'autre que
  les actions décrites par l'utilisateur ne peut être lancé.

## Alternatives écartées

- **Deux agents hôte séparés** (un pour le son, un pour les actions) : double
  installation et double maintenance pour aucun gain.
- **Exécuter les actions depuis un conteneur privilégié** : n'atteint ni les
  enceintes ni le bureau de l'hôte, surtout sous WSL — la barrière est réelle,
  pas une question de privilèges.
- **Mettre le TTS dans le Pont** : dupliquerait la pile voix (modèles, cache) sur
  l'hôte ; le Pont doit rester léger et sans intelligence.
- **Opérateur libre / commandes arbitraires** : refusé au grilling. Le catalogue
  est fermé ; l'assistant n'a jamais accès à un shell.

## Addendum 2026-07-03 — jeton partagé

Écouter sur `0.0.0.0` (nécessaire pour `host.docker.internal`) expose aussi le
Pont au LAN — le NAT de WSL2 protège par accident, plus du tout en réseau
« mirrored ». Un **jeton partagé** (`HOST_BRIDGE_TOKEN`, header `X-Bridge-Token`,
comparaison en temps constant) est donc exigé sur toutes les routes sauf
`/health` dès qu'il est défini ; le Time Forge le présente
(`TIME_FORGE_HOST_BRIDGE_TOKEN`, injecté par le compose depuis le `.env` non
versionné). Jeton vide = auth désactivée, réservé au dev local sur `127.0.0.1`.
Un reverse proxy (nginx/Caddy) a été écarté : aucun service n'est exposé
au-delà du loopback, il n'y a pas de frontière réseau à protéger — à
re-grillinger le jour d'un accès distant (téléphone, LAN).
