# Handoff 0016 — Carte wayfinder + chaîne voix débuggée maillon par maillon (premier tour de parole imminent)

> Convention : handoffs dans `docs/handoffs/`, seul le plus récent fait foi.
> En fin de session, générer le 0017 via `/handoff`.

Dates : session entamée le 2026-07-10 (cadrage + carte), reprise en continu
jusqu'au **2026-07-16** (débogage live du run réel avec l'utilisateur au poste
Windows). Remplace le 0015. **RIEN N'EST COMMITÉ** — l'arbre de travail est
volumineux (voir §Git).

## Le fait central : la carte wayfinder fait foi

Le pilotage du chantier « redémarrage clean → stack qui parle » vit dans
**`docs/wayfinder/`** (carte + 11 tickets, tracker markdown local — conventions
dans son README). Lire `docs/wayfinder/carte.md` AVANT ce handoff : destination,
notes (dont : subagents autorisés à télécharger ≤ 3 Go), 4 décisions actées
(ménage, voix par tour, expérience déménagement **réussie**, recherche mot
d'éveil), fog et hors-périmètre. Le détail de chaque décision vit dans son
ticket, pas ici.

## État au moment du handoff : le run réel (ticket 0003) à un cheveu du but

Session de débogage live : chaque clic de l'utilisateur a levé un piège, chacun
corrigé puis re-testé. Chaîne validée dans les logs réels
(`logs-tests/transport.log`, encodage UTF-16 → lire via
`iconv -f UTF-16LE -t UTF-8`) :

- **Coquille → transport** : CORS ajouté (l'origine réelle du dev Tauri est
  `http://127.0.0.1:1430`, attrapée par le filet regex `cors_origine_regex`).
- **TTS voice-forge** : accueil **audible et propre**. Cause du grésillement
  initial : WAV **float32, données à l'offset 80** vs helper Pipecat qui
  suppose PCM16/en-tête 44 o → `NormaliseurWavPCM16` côté transport
  (+ fix source `chatterbox.py` en PCM_S 16 bits, **effectif seulement au
  prochain rebuild de l'image voice-forge**).
- **Micro → VAD → STT** : transcriptions françaises parfaites (TTFB 0,4-1,1 s).
  Cause de la surdité initiale : **Pipecat 1.5 ignore `vad_analyzer=` dans
  `TransportParams`** — impasse détaillée dans `docs/impasses.md` (2026-07-16),
  fix = `VADProcessor` explicite dans le pipeline.
- **Dialogue Forge** : 404 « persona inconnu » → piège documenté du montage
  vide post-reboot (le `restart` ne suffit PAS, il faut
  `docker compose up -d --force-recreate dialogue`). Personas rechargés.
- **Timeout httpx** : le défaut 5 s tuait le stream du premier tour à froid
  (prefill LLM ~13 s mesuré, LLM sain à 0,8 s à chaud, PAS paginé) →
  `httpx.Timeout(10.0, read=120.0)` dans `ClientDialogueREST`.
- **Voix du persona** : `personas/assistant.md` passé « Emma » →
  « VoixDeTest » (Emma n'est pas enrôlée ; depuis le fix voix-par-tour elle
  aurait été réellement demandée → 400). Provisoire jusqu'au ticket 0005.

**Dernier geste demandé à l'utilisateur** : relancer le transport et dire
« Quelle heure est-il ? ». S'il entend la réponse → premier tour complet de la
nouvelle stack. Restent alors à qualifier : multi-tours, fin par silence
(fenêtre d'écoute de suite → `/clore`), **interruption** (jamais testée — le
câblage 1.5 des tours/interruptions est à vérifier : le pipeline n'a pas de
processeur de tours explicite, seulement le VADProcessor), événements RTVI
réels (pour le ticket 0007 pastille). Puis résoudre le ticket 0003 (compte
rendu + mesures vs 2,88 s de l'ancienne stack).

## Git — tout est en attente de commit (l'utilisateur commite)

Modifiés : `.gitignore`, `docker-compose.yml`, `scripts/download-models.sh`
(ménage) ; `transport-voix/` (config, main, rest, pipecat, dialogue_processor,
tts_voiceforge + nouveaux `selecteur_voix.py`, `normaliseur_wav.py` et 4
fichiers de tests) ; `voice-forge/app/providers/chatterbox.py` ;
`personas/assistant.md`. Supprimés : `openwebui/`, `coturn/`,
`docker-compose.sans-stt.yml`, `stt/template-transcription.jinja` (dossier vide
orphelin). Nouveaux non suivis : `docs/wayfinder/`, `docs/impasses.md` (entrée
ajoutée), ce handoff, `logs-tests/` (à ajouter au `.gitignore` ou vider —
**non tranché**). Tests : transport-voix 22 verts + ruff ; voice-forge 33
verts + ruff ; « texte du commit » = commandes git complètes, découper par
lots (ménage / transport / voice-forge / wayfinder+docs).

## Reste à faire hors chemin critique (commandes utilisateur)

- `docker compose up -d --remove-orphans` — les conteneurs openwebui/coturn
  tournent encore (orphelins depuis le ménage).
- `docker compose build memory && docker compose up -d memory` — l'image date
  d'avant `/viz` et `/graph/complet` (404 dans le conteneur, découvert au
  ticket déménagement).
- `docker compose build voice-forge && docker compose up -d voice-forge` —
  pour rendre effectif le fix PCM16 à la source (le normaliseur transport
  couvre en attendant ET après : il laisse passer le PCM16 tel quel).
- Étendre `scripts/demarrage-hote.sh` : il ne répare que le montage `voices/`
  de voice-forge ; le même piège vient de frapper `personas/` du service
  `dialogue` — généraliser la vérification (non fait, non tické).

## Vigilances

- **Décalage de dates** : la carte et plusieurs résolutions disent
  « 2026-07-10 » ; le débogage live s'est fait le 2026-07-16. Les faits du
  graphe mémoire (Paris/Lyon) datent du 10 — ils sont TOUJOURS en place
  (matière d'audit `/viz`, ne pas purger sans réfléchir).
- Tickets frontière restants : 0002 docs racine v2 (**débloqué**, délégable),
  0005 vraie voix (HITL), 0007 RTVI pastille et 0010 mot d'éveil (bloqués par
  la clôture de 0003), 0008 module dialogue, 0011 recette finale.
- Toute modification WSL du code transport exige un **redémarrage du process
  Windows** (`Ctrl+C` + relance ; il lit `\\wsl.localhost`).
- Le test d'intégration Pipecat gaté (`importorskip`) n'a jamais tourné ;
  la dérogation de voix en réel attend une 2e voix enrôlée.
- LLM : premier appel à froid ~13 s (cache de préfixe), ~0,8-1,3 s ensuite —
  ne pas re-diagnostiquer une pagination sur ce seul symptôme.

## Suggested skills

- `/impasses` — en ouverture : 2 entrées récentes (VAD Pipecat 1.5, et relire
  celle du TTS 2026-07-09 complétée par le float32).
- `/premisses` — avant de continuer le run réel : stack debout ? montages
  pleins (`docker compose exec dialogue ls /personas`) ? transport relancé
  après les derniers fixes ?
- `/delegate` — ticket 0002 (docs racine v2) est le prochain lot AFK propre.
- `/handoff` — générer le 0017 en fin de session.
