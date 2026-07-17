# Handoff 0017 — Quatre tickets clos en une session ; réglage grand public validé au réel

> Convention : handoffs dans `docs/handoffs/`, seul le plus récent fait foi.
> En fin de session, générer le 0018 via `/handoff`.

Session du 2026-07-17 au 2026-07-18 (nuit), utilisateur au poste Windows en
HITL continu. Remplace le 0016. **RIEN N'EST COMMITÉ** au moment d'écrire —
les deux commandes de commit (0013 seul, puis 0014 + code) ont été fournies à
l'utilisateur en fin de session ; vérifier `git log` avant de s'y fier.

## Le fait central : il ne reste que 2 tickets sur la carte

Quatre tickets clos cette session — le détail de chaque clôture vit dans le
ticket, pas ici (`docs/wayfinder/tickets/`) :

- **0005** capture micro navigateur — validée au réel (WebM/Opus →
  `decodeAudioData` → WAV PCM16 passe en vrai navigateur).
- **0012** clonage réel Chatterbox — **la prémisse du ticket était fausse** :
  tout était déjà en place (extra chatterbox + torch 2.8/cu128 dans l'image,
  sm_120 capability (12,0), poids présents, ~1,75 s en régime). Aucun
  téléchargement n'a eu lieu. Validé à l'oreille.
- **0013** contrat cross-forge voix — décision : **le DF proxie voice-forge**
  (`GET /voix`), contrat complet documenté dans le ticket.
- **0014** réglage grand public — prototype 3 variantes → variante B retenue
  (formulaire), **modèle A retenu : préférence permanente persistée**.
  Implémentation déléguée à un subagent sonnet, vérifiée, puis **validée au
  réel** : l'utilisateur a réglé persona assistant + voix Jackie depuis
  l'onglet Réglages de la coquille, et l'assistant répond en Jackie.

Restent : **0011** (recette finale ACCEPTANCE v2 — le portail de la
destination) et **0015** (bascule des consommateurs vers la vraie voix).
Les deux sont débloqués.

## Ce qui a changé dans le code (session 0014, tout dans le commit à venir)

- `dialogue-forge/app/voix/` — port `CatalogueVoix` + factice + REST
  (validé en réel) ; `app/preferences.py` (préférence persistée JSON) ;
  `app/routes/reglage.py` + page `app/reglage/` ; `GET /voix` +
  `POST /voix/{id}/apercu` + adoption de la préférence dans
  `creer_conversation` (`app/routes/api.py`). 54 tests verts, ruff clean.
- `coquille/src/` — navigation Console/Réglages (`nav.js` **externe** : la CSP
  `script-src 'self'` interdit l'inline), second iframe `/reglage`, les deux
  iframes restent montées (canal RTVI préservé).
- `docker-compose.yml` — service dialogue : `DIALOGUE_FORGE_VOIX_BACKEND=rest`,
  `DIALOGUE_FORGE_VOICE_FORGE_URL`, `DIALOGUE_FORGE_REGLAGE_PATH=/data/reglage.json`,
  volume `dialogue-forge-data`.
- Le conteneur `dialogue` a été **reconstruit et tourne** avec ce code
  (`docker compose up -d --no-deps --build dialogue` — `--no-deps` obligatoire,
  cf. impasse 2026-07-17 sur la reconstruction en cascade).

## État runtime au moment du handoff

- Stack Docker WSL : tous les services healthy (LLM 8001 ~32 tok/s mesuré,
  STT 8002, voice-forge 8100 avec Chatterbox chargé, DF 8600).
- Transport-voix + coquille : lancés au poste Windows par l'utilisateur.
  **Nouveau confort** : variables d'env posées en permanent (`User`) via
  `SetEnvironmentVariable` (les 4 `TRANSPORT_VOIX_*_BACKEND`,
  `UV_PROJECT_ENVIRONMENT`, `CARGO_TARGET_DIR`), et lancement **une fenêtre,
  deux volets** :
  `wt -d …\transport-voix powershell -NoExit -Command "uv run --extra pipecat python -m app" `` `; `` split-pane -V -d …\coquille powershell -NoExit -Command "cargo tauri dev"`
  (piège : `wt` coupe sur TOUT `;`, même entre guillemets — d'où `-d` au lieu
  de `cd` ; pas encore consigné dans impasses.md).
- Préférence active : `{"persona":"assistant","voix":"Jackie"}`.

## Anomalies relevées, à qualifier en 0011 (pas des blocages)

1. **La boucle d'outils MCP ne se déclenche pas toujours** : sur « donne-moi
   l'heure », le LLM a halluciné « quatorze heures vingt-trois » (il était
   00h25) au lieu d'appeler time-forge. Reproduit en direct via
   `POST /conversations/{id}/tours`. À instruire (prompt d'outils ? modèle ?).
2. **Voix Jackie ~-12 dB** sous les autres (amplitude max 8319/32768 sur une
   synthèse ; clonek sature à 32768). Piste : normalisation du `speaker.wav`
   à l'enrôlement (voice-forge).
3. Premier tour après démarrage : ~41 s (chargement Chatterbox à froid) —
   documenté, pas un défaut ; à intégrer aux mesures de la recette.

## Pièges frais (au-delà du registre docs/impasses.md — le consulter d'abord)

- `docker compose exec <svc> python` vise le Python de **base** de l'image,
  pas le `.venv` uv de l'app : pour sonder les paquets réels, passer par
  `docker compose exec <svc> uv run --no-sync python …` (c'est ce piège qui
  faisait croire chatterbox absent au début du 0012).
- Le TTFB TTS à ~6 ms dans les logs Pipecat = **cache voice-forge**, pas une
  anomalie.

## Suggested skills

- `/premisses` avant d'attaquer 0011 ou 0015 — cette session a encore prouvé
  que les prémisses des tickets peuvent être mortes (0012 : tout le travail
  « restant » était déjà fait).
- `/impasses` — consulter avant tout diagnostic ; capturer à chaud le piège
  `wt`/`;` ci-dessus si l'occasion se présente.
- `/newbie` pour toute commande destinée à l'utilisateur (topologie du
  CLAUDE.md fait foi).
- `/delegate` pour les gros lots d'implémentation (a bien fonctionné sur le
  0014 : brief sourcé + vérification par l'agent principal).
- `/handoff` en fin de session (générer le 0018).

## Par où commencer

1. Vérifier `git log` : les commits 0013 et 0014 fournis à l'utilisateur
   sont-ils passés ? Sinon, les redonner (mémoire : commande git complète,
   jamais de Co-Authored-By).
2. Choix utilisateur : **0015** (bascule des consommateurs — prolongement
   naturel, la vraie voix est prouvée) ou **0011** (recette finale — y
   intégrer les 2 anomalies ci-dessus). Le 0011 clôt la carte.
