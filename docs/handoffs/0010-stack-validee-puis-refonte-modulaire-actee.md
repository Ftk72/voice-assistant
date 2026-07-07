# Handoff 0010 — Stack OpenWebUI validée de bout en bout, puis refonte modulaire actée (ADR 0009) : le prochain chantier est le Dialogue Forge

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent fait foi. En fin de session, générer le 0011 via `/handoff`.

Date : 2026-07-07 · Remplace le 0009. Session couverte : réparation complète de la chaîne vocale (5 bugs de fond), validation réelle de tout ce qui était validable, remise à zéro des mémoires, audit d'acceptation, préparation Qwen3-TTS, puis **grilling décisif : sortie d'OpenWebUI** (ADR 0009). **Rien n'est commité** — l'arbre porte toute la session (l'utilisateur commite ; un texte de commit intermédiaire a été fourni en cours de session, il ne couvre pas les changements postérieurs : adaptateur qwen3tts, ADR 0009, CONTEXT.md, CLAUDE.md, plan-de-tests, mesure-latence).

## Lire avant tout (fait autorité)

- `CLAUDE.md` (réaligné ADR 0009) · `CONTEXT.md` (réécrit : Conversation, Dialogue Forge, Transport voix, Coquille, Module d'interface, Mot d'éveil) · **`docs/adr/0009-sortie-openwebui-architecture-modulaire.md`** — LA décision qui gouverne la suite, avec toutes les alternatives écartées.
- **`docs/impasses.md`** — 4 entrées neuves de cette session (KV Voxtral sans `-c`, template Devstral dans le GGUF, coercition ASR par prompt, OOM de build `-j` qui tue WSL). Les impasses OpenWebUI deviennent caduques pour la nouvelle stack mais restent vraies pour l'ancienne.
- `docs/plan-de-tests.md` — écrit pour la stack OpenWebUI le matin même, **caduc côté interface** depuis l'ADR 0009 ; les critères ACCEPTANCE restent la cible.

## État réel constaté en fin de session

- **L'ancienne stack tourne encore** (10 services healthy + Pont hôte) : OpenWebUI n'a PAS encore été retiré du compose — le big bang est décidé, pas exécuté. Elle a été **validée de bout en bout** avant décision : conversation vocale au micro OK, mémoire Léa OK de vive voix, annonce sur enceintes OK (smoke-test `POST /announce`), chaîne Time→VoiceForge→Pont→aplay prouvée.
- **Mesures de référence** (`scripts/mesure-latence.sh`, stimulus propre) : voix→voix **2,88 s** (STT 0,30 + LLM 1ʳᵉ phrase 0,86 + TTS 1,72) vs critère ≤ 2 s — le TTS non streamé est le mur ; STT whisper.cpp sm_120 excellent (0,1-0,5 s, compilé localement `stt/Dockerfile`, `-j 4` impératif).
- **Mémoires remises à zéro à la demande** : graphe Neo4j vidé (0 nœud), documents/ purgé, 20 chats OpenWebUI supprimés. Terrain vierge pour la nouvelle stack — c'est ce qui rend le swap d'embedder gratuit maintenant.
- **Qwen3-TTS préparé mais JAMAIS exécuté** : poids dans `models/qwen3-tts/` (base + tokenizer), adaptateur `_RealQwen3TTSEngine` écrit en TDD (32 tests verts, extras uv `chatterbox`/`qwen3tts` déclarés conflictuels, `ARG TTS_EXTRA` au Dockerfile), **image jamais rebuildée, moteur jamais lancé** — risques ouverts : sm_120, résolution du tokenizer audio par le paquet `qwen-tts`.
- Pont hôte : `SystemPlayer` (aplay/WSLg) validé en réel ; prérequis audio installés à la main (`pulseaudio-utils alsa-utils libasound2-plugins` + `/etc/asound.conf`) ; `scripts/demarrage-hote.sh` répare la stack au boot (montage voices vide, LLM en dernier, lancement du Pont). Le lanceur `.vbs` du dossier Démarrage Windows devait être posé par l'utilisateur — statut incertain, à vérifier.

## Ordre de construction proposé (validé en fin de grilling, non commencé)

1. **Swap embedder** : bge-m3 → `Qwen/Qwen3-Embedding-0.6B-GGUF` (~640 Mo, l'utilisateur télécharge) — piège connu : `--pooling last` sur llama-server, sinon embeddings de tokens.
2. **Dialogue Forge** texte seul (nouveau forge, modèle memory-forge) : historique, injection/extraction mémoire en REST, outils en client MCP, personas — testable au curl sans audio.
3. **Pipecat + mot d'éveil** (openWakeWord, choix utilisateur v1 contre recommandation — repli documenté : bouton d'abord) branché sur le Dialogue Forge.
4. **Coquille Tauri** (Rust) : carte son WebRTC + assemblage des modules servis par les forges.
5. **Retrait d'OpenWebUI** du compose (l'image reste sur disque en secours).

## Pièges à connaître (au-delà du registre)

- Trois choix utilisateur assumés **contre recommandation** : big bang, interruption illimitée, mot d'éveil v1 — documentés dans l'ADR 0009, ne pas les rediscuter sans nouveau grilling.
- Toute la section « Plateforme » du CLAUDE.md (sm_120, `-j` borné, LLM en dernier, montages au boot) : chèrement acquise aujourd'hui, la relire avant toute manip GPU/build.
- `host-bridge/catalog.toml` (copie de l'exemple) est volontairement non versionné ; runner encore `fake`.

**Prémisses différées** : `_RealQwen3TTSEngine` (jamais lancé) ; qualité du clonage Qwen3-TTS sur vraie voix française ; faisabilité mot d'éveil français (openWakeWord) ; transport WebRTC Tauri↔Pipecat jamais prototypé ; `.vbs` de démarrage posé ou non ; vraie voix toujours pas enrôlée (VoixDeTest partout, y compris `TIME_FORGE_ANNOUNCE_VOICE`).

## Méthode de travail (inchangée — CLAUDE.md)

Analyser → proposer → attendre validation → TDD → doc. Tout en français. Jamais de `git commit` par l'agent, jamais de Co-Authored-By ; « texte du commit » = commande git complète. Gros téléchargements lancés par l'utilisateur, dépôts/tags vérifiés par API avant de donner une commande.

## Suggested skills

- `/premisses` — en ouverture : la stack tourne-t-elle encore ? l'utilisateur a-t-il commité ? le `.vbs` est-il posé ? les poids qwen3-tts/embedder sont-ils là ?
- `/impasses` — consulter avant tout diagnostic ; capturer à chaud (4 entrées aujourd'hui, le registre paie).
- `/tdd` — le Dialogue Forge se construit comme memory-forge, tests d'abord.
- `/delegate` — lots bornés (le banc de latence d'aujourd'hui en est un bon exemple) ; jamais pour ce qui dépend du contexte de session.
- `/grilling` — au premier écart au plan de l'ADR 0009, ou pour dessiner l'API du Dialogue Forge avant de coder.
- `/handoff` — générer le 0011 en fin de session.
