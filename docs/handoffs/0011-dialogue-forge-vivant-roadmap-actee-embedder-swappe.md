# Handoff 0011 — Dialogue Forge construit, validé et optimisé ; roadmap + ADR 0010 actés ; graphe 3D livré ; embedder swappé

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent
> fait foi. En fin de session, générer le 0012 via `/handoff`.

Date : 2026-07-08 (session du 07 au 08) · Remplace le 0010. Session couverte :
construction complète du Dialogue Forge (délégations sonnet/opus vérifiées),
premier essai réel des trois adaptateurs, résolution du goulot de latence
(cache de préfixe llama.cpp), correction du recall halluciné, purge du graphe,
grilling UI/roadmap (ADR 0010, `docs/roadmap.md`), front B1 (graphe mémoire 3D)
livré et validé de visu par l'utilisateur, swap embedder exécuté et validé.
**Rien n'est commité** — l'arbre porte toute la session (l'utilisateur commite).

## Lire avant tout (fait autorité)

- `docs/roadmap.md` — **LE document de pilotage** né du grilling : deux fronts
  parallèles (A voix, B modules UI), suites par coût croissant, idées SOTA en
  réserve, contraintes matérielles en tête.
- `docs/adr/0010-ui-coquille-console-pastille.md` — les 7 décisions UI
  (console + pastille, audio par la webview, persona pilote/voix déroge,
  texte après amorce vocale via RTVI, 3d-force-graph, deux fronts).
- `CONTEXT.md` — enrichi : **Console**, **Pastille**, règle persona/voix.
- `dialogue-forge/README.md` — l'orchestrateur : API, variables, latences.

## État réel constaté en fin de session

- **Dialogue Forge (`dialogue-forge/`, port 8600) : construit, validé en réel,
  optimisé.** 24 tests verts, ruff propre. Les trois adaptateurs réels
  (`MoteurLLMOpenAI`, `MemoireREST`, `OutilsMCP`) **validés en réel le
  2026-07-07** contre la stack. Latence première phrase : ~1,2 s à chaud
  (préfixe stable : système constant = persona + `CONSIGNES_OUTILS`, outils
  fixés au démarrage, faits mémoire en message `user` persisté, boucle
  d'outils persistée dans l'historique) ; ~3-5,5 s à froid (prefill MoE,
  incompressible sans `--cache-reuse` côté llm — option D non engagée).
  Le recall est appelé (plus d'hallucination mémoire) grâce au bloc de
  consignes constant. **Pas de serveur MCP exposé ni d'UI** (écarts assumés).
- **Graphe Neo4j purgé le 2026-07-07** (0 nœud, vérifié) après découverte
  clé : une hallucination capturée en épisode était devenue un faux fait
  restitué par recall. Question ouverte : filtrer ce qui se mémorise
  (dires de l'assistant vs de l'utilisateur) — grilling à prévoir avant le
  branchement mémoire réelle définitif.
- **Front B1 livré** : module `/viz` de memory-forge refondu en 3D
  (3d-force-graph 1.80.0 **vendoré**, `app/viz/vendor/`), communautés par
  propagation d'étiquettes maison (`app/viz/analyse.py`), endpoint
  `GET /graph/complet`, filtres provenance/obsolètes, bascule 2D/3D, oubli
  depuis la vue. 64 tests verts. **Validé visuellement par l'utilisateur**
  (port local 8201). Le conteneur Docker sert l'ancienne page **jusqu'au
  rebuild de l'image memory** (à faire, `-j` borné hors sujet ici : image
  Python simple).
- **Embedder swappé et validé en réel le 2026-07-08** : service `embedder`
  du compose sur `Qwen3-Embedding-0.6B-Q8_0.gguf` (CPU) avec
  `--pooling last` (piège documenté : sans lui, embeddings de tokens).
  Vérifié : un vecteur par phrase, dim 1024 (comme bge-m3), sémantique
  cohérente (0,674 proche vs 0,277 éloigné). Conteneur recréé, healthy.
  `bge-m3-q8_0.gguf` reste sur disque (supprimable).
- **La stack tourne** (OpenWebUI toujours dans le compose — retrait = front
  A5, pas encore fait). Le graphe est quasi vierge : seuls des épisodes du
  banc B1 en backend fake (rien en prod) ; de nouveaux épisodes réels ne
  doivent arriver qu'après décision sur le filtrage mémoire.

## Fronts de la roadmap — où on en est

- **A1 swap embedder : FAIT.** A2 (Pipecat + mot d'éveil) : **prochain gros
  chantier** — prémisse à lever tôt : prototype WebRTC WebView2↔Pipecat
  (jamais testé). A3 coquille, A4 module dialogue, A5 retrait OpenWebUI :
  non commencés.
- **B1 graphe 3D : FAIT** (reste le rebuild de l'image memory). B2 module
  voix/enrôlement, B3 agenda, B4 notifications d'annonces : non commencés.

## Pièges et acquis de session (au-delà du registre)

- **Préfixe stable = loi** : tout octet variable en amont du prompt re-paie
  du prefill lent (MoE en RAM). Toute nouvelle consigne doit être constante ;
  toute injection se fait en aval, persistée. Ne pas casser ça.
- Un tour LLM est **soit texte, soit appels d'outils** (convention documentée
  dans le port `MoteurLLM`).
- Les délégations marchent bien sur ce dépôt (4 lots cette session, briefs
  autoportants avec chemins absolus + validation au banc réel) ; toujours
  contre-vérifier soi-même (un subagent a présenté un faux fait mémorisé
  comme une validation).
- Épisodes de test : utiliser la **mémoire factice** dans les bancs réels
  (leçon de la pollution du graphe).

## Prémisses différées (à vérifier, pas à croire)

`_RealQwen3TTSEngine` toujours jamais exécuté ; faisabilité mot d'éveil
français (openWakeWord) ; WebRTC WebView2↔Pipecat jamais prototypé ; vraie
voix toujours pas enrôlée (VoixDeTest partout) ; `.vbs` de démarrage Windows
posé ou non ; `GraphitiMemory.graphe_complet` (Cypher) jamais exécutée ;
image memory pas rebuildée (le /viz 3D n'est pas encore servi par Docker).

## Méthode de travail (inchangée — CLAUDE.md)

Analyser → proposer → attendre validation → TDD → doc. Tout en français.
Jamais de `git commit` par l'agent ; « texte du commit » = commande git
complète. Gros téléchargements lancés par l'utilisateur (dépôt/fichier
vérifiés par API avant de donner la commande). Délégations : brief
autoportant, vérification finale par l'agent principal.

## Suggested skills

- `/premisses` — en ouverture : l'utilisateur a-t-il commité ? la stack
  tourne-t-elle ? l'image memory a-t-elle été rebuildée ?
- `/impasses` — consulter avant tout diagnostic ; capturer à chaud.
- `/grilling` — avant le branchement mémoire réelle (que mémorise-t-on ?)
  et pour dessiner l'API Pipecat↔Dialogue Forge (front A2).
- `/tdd` — tout nouveau composant (transport voix) se construit comme
  memory-forge/dialogue-forge.
- `/delegate` — lots bornés avec banc de validation réel ; mémoire factice
  dans les bancs.
- `/handoff` — générer le 0012 en fin de session.
