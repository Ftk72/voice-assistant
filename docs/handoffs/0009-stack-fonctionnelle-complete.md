# Handoff 0009 — Stack fonctionnellement complète : TTS débloqué (sm_120), mémoire ambiante et outils MCP branchés dans OpenWebUI ; reste le présentiel (voix réelle, mode appel)

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent fait foi. En fin de session, générer le 0010 via `/handoff`.

Date : 2026-07-06 · Remplace le 0008. Session couverte : configuration OpenWebUI (compte, audio, Filter, MCP), déblocage des outils MCP (trois impasses), validation de la boucle mémoire ambiante dans les deux sens, première synthèse TTS réelle (échec sm_120 puis déblocage torch 2.8/cu128 le jour même). **Tout est commité par l'utilisateur** — commits `4654171..adab27c` (lire `git log 4654171..adab27c`, messages détaillés) ; arbre propre.

## Lire avant tout (fait autorité)

- `CLAUDE.md` · `CONTEXT.md` · `docs/adr/` · `docs/ACCEPTANCE*.md` · `docs/OPENWEBUI.md`
- **`docs/impasses.md`** — 2 entrées neuves de cette session : les **3 pièges silencieux des connexions MCP OpenWebUI** (auth Bearer à clé vide, Function Name Filter = liste blanche, toolIds transmis par le frontend seul) et l'impasse **sm_120 marquée PÉRIMÉE** (levée par `override-dependencies` torch 2.8/cu128 — le commentaire du pyproject documente tout).

## État : tout fonctionne, prouvé en réel

- **10 services healthy + Pont hôte** (hors Docker, port 8500 — à relancer après reboot, cf. 0008).
- **TTS Chatterbox opérationnel sur la RTX 5080** : synthèse 41 s à froid (chargement), **1,94 s en régime** (critère ≤ 2 s tenu), 10 ms sur cache, VRAM 14,6/16,3 Go avec le LLM chargé. Voix factice **« VoixDeTest »** laissée enrôlée (qualité robotique voulue — wav synthétique) pour que le sélecteur TTS d'OpenWebUI ne soit pas vide.
- **OpenWebUI configuré et branché** (compte admin créé ; config PersistentConfig = base sqlite du volume, PAS les variables du compose désormais) :
  - Outils MCP `recall`/`forget` **fonctionnels en conditions réelles** (appel natif prouvé : recall → faits Léa+document restitués). 3 connexions : memory (attachée au persona « assistant »), time et world (réparées, à attacher aux personas au besoin).
  - **Filter mémoire validée dans les deux sens** : inlet (injection des faits en contexte sans outil) et outlet (conversation → épisode → extraction → fait retrouvable). Attachée au persona « assistant » uniquement.
  - Persona « assistant » : system prompt court de l'utilisateur (pas celui de `personas/assistant.md` — à son choix), function_calling `native`, Filter + outil mémoire.
- **Correctifs code de la session** (tout TDD, tout vert) : `transport_security` MCP dans les 4 forges (421 depuis le réseau Docker), `GET /v1/models` dans voice-forge (404 UI audio), override torch dans `voice-forge/pyproject.toml`.
- Le graphe contient toujours le **jeu de démo Léa/judo/document** (Neo4j Browser `:7474`, `/viz` sur `:8200`).

## Pièges à connaître (le détail est dans impasses.md et les commits)

- Toute intervention sur la config OpenWebUI post-premier-démarrage = éditer sa base sqlite (`/app/backend/data/webui.db` dans le conteneur) ou l'UI — les variables du compose sont ignorées. Patterns éprouvés dans cette session : JWT admin forgé depuis `/app/backend/.webui_secret_key` pour appeler l'API comme le navigateur ; `GLOBAL_LOG_LEVEL=DEBUG` temporaire pour voir les erreurs avalées.
- Les `toolIds`/`filterIds` d'un modèle s'appliquent au chat **neuf** ouvert depuis le frontend ; l'API directe sans `tool_ids` ne les porte pas.
- `Context size exceeded` croisé une fois (contexte 8192) : options documentées en conversation — réduire ce qui remplit le contexte, `-c 12288` (VRAM à surveiller), quantifier le cache KV.

## Reprendre ici (essentiellement du présentiel utilisateur)

1. **Mode appel au micro** : bouton d'appel dans un chat avec le persona « assistant » — c'est le test bout-en-bout (VAD → Voxtral → LLM → Chatterbox) et la mesure de latence totale ≤ 2 s. Presets casque/haut-parleurs : `docs/OPENWEBUI.md`.
2. **Enrôler la vraie voix** sur `http://127.0.0.1:8100/admin`, la choisir dans le persona (champ TTS Voice), supprimer « VoixDeTest ».
3. **Scénarios d'acceptation de vive voix** (`docs/ACCEPTANCE-MEMOIRE.md`) : scénario Léa au micro, oubli oral, persona off-record (à créer : mêmes réglages sans Filter ni outils), visualisation.
4. Chantiers non urgents hérités : dédoublonnage des nœuds `Episodic` à la ré-ingestion, extraction 4/5 → 5/5 sur épisode court, latence STT jamais mesurée, `models/voxtral-tts-q4.gguf` (ADR à faire si exploré).

**Prémisses différées** : latence bout-en-bout en mode appel (jamais mesurée, seuls les maillons individuels le sont : LLM 0,7 s, TTS 1,9 s, search 25 ms) ; qualité du clonage Chatterbox sur une vraie voix française ; comportement de la Filter en conversation longue (le 8192 peut déborder).

## Méthode de travail (inchangée — CLAUDE.md)

Analyser → proposer → attendre validation → TDD → doc. Tout en français. Jamais de `git commit` par l'agent, jamais de Co-Authored-By. Aucun téléchargement lourd sans accord explicite au moment même. L'utilisateur privilégie `/delegate` (briefs détaillés, vérification indépendante par l'agent principal, `SendMessage` pour prolonger un subagent) — attention aux **limites de session** qui peuvent couper un subagent en vol : constater l'état réel avant de relancer, reprendre inline si besoin.

## Suggested skills

- `/premisses` — en début de session : stack encore up ? Pont hôte relancé ? VoixDeTest toujours là ?
- `/impasses` — consulter avant tout diagnostic (les pièges OpenWebUI y sont) ; capturer à chaud.
- `/verify` ou `/run` — pour le test du mode appel si l'agent y participe.
- `/delegate` — lots bornés, comme cette session.
- `/handoff` — générer le 0010 en fin de session.
