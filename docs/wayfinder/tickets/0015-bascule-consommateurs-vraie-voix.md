---
label: wayfinder:task
statut: clos
assigne: agent principal (session 2026-07-18)
bloque-par: [0012-clonage-reel-de-la-voix, 0005-enrolement-de-la-vraie-voix]
---

# Basculer tous les consommateurs sur la vraie voix

## Question

Ex-étapes 2 et 3 de l'ancien 0005, isolées au re-wayfinding 2026-07-17 : une
fois la vraie voix **enrôlée** (0005) et le clonage **audible pour de vrai**
(0012), sortir toute **VoixDeTest** du chemin nominal.

1. **Basculer les consommateurs** : `TIME_FORGE_ANNOUNCE_VOICE`, la voix par
   défaut du transport (`tts_voix_defaut`), les personas concernés
   (`personas/*.md`, `meta.tts.voice`) — plus aucune VoixDeTest en chemin
   nominal.
2. **Vérifier à l'oreille** : une **annonce time-forge sur les enceintes**
   (chemin Pont hôte / aplay-WSLg, validé sur l'ancienne stack) restitue la
   vraie voix.

Bloqué tant que 0012 (le clone doit être audible pour de vrai) et 0005 (la vraie
voix doit être enrôlée) ne sont pas clos.

## Périmètre

- Réglages/env des consommateurs + personas ; vérification annonce enceintes.
- **Hors périmètre** : le réglage grand-public interactif (0014) — ici c'est la
  **valeur par défaut système** qui bascule.

## Critère de clôture

Une annonce time-forge sur les enceintes parle avec **la vraie voix**, et aucun
chemin nominal ne référence plus une VoixDeTest.

## Clôture (session 2026-07-18)

**Choix de la voix par défaut tranché par l'utilisateur : `Jackie`** (parmi les
voix enrôlées `clonek`/`Jackie`/`Jackie Chan`/`EchantillonTest` — ambigu, donc
posé en question plutôt que supposé). Le libellé du ticket (« `meta.tts.voice` »)
était périmé : le format réel est le titre `# Nom (voix : X)`, parsé par
`dialogue-forge/app/personas.py`.

Trois consommateurs basculés :

- `docker-compose.yml` — `TIME_FORGE_ANNOUNCE_VOICE: Jackie`.
- `transport-voix/app/config.py` — `tts_voix_defaut: str = "Jackie"`.
- `personas/assistant.md` — `# Assistant (voix : Jackie)`.

Laissés en l'état (hors chemin nominal, convention ports/adaptateurs) :
`dialogue-forge/app/voix/fake.py` et les tests (`test_voix.py`,
`test_tts_voiceforge_pipecat.py`, `test_selecteur_voix.py`) qui utilisent
`VoixDeTest` comme valeur factice générique, pas comme réglage de production.
`personas/batman.md` référence une voix `Batman` non enrôlée — hors périmètre
(ce n'est pas VoixDeTest).

**Piège frais rencontré à la vérification** : le premier essai d'annonce a
échoué en silence côté enceintes — `time` levait `httpx.ConnectError` vers le
Pont hôte (`host.docker.internal:8500`, HTTP 000). Cause : le Pont hôte
(hors Docker, ADR 0008) n'était pas démarré (piège de boot déjà documenté au
CLAUDE.md/`scripts/demarrage-hote.sh`, mais pas encore dans `docs/impasses.md`
en tant que tel). Relancé manuellement (`cd host-bridge && uv run python -m
app` en arrière-plan) : `/health` répond, l'annonce suivante a joué
`Playing WAVE ... POST /play 202` dans les logs du Pont hôte.

**Validé à l'oreille par l'utilisateur le 2026-07-18** : annonce time-forge
sur les enceintes (`curl -X POST http://127.0.0.1:8400/announce -d
'{"text":"Essai de la vraie voix."}'`), voix Jackie confirmée entendue.

Débloque **0011** (recette finale — dernier ticket restant sur la carte).
