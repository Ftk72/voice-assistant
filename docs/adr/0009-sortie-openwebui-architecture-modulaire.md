# ADR 0009 — Sortie d'OpenWebUI : architecture modulaire (Dialogue Forge, transport voix, coquille)

Date : 2026-07-07 · Statut : accepté · Remplace l'ADR 0003 (et l'hypothèse
« OpenWebUI unique interface » qui traversait les ADR 0001-0008)

## Contexte

Dix jours de construction ont validé la stack de bout en bout (voix, mémoire,
annonces), mais le registre des impasses est éloquent : **zéro impasse dans le
code custom (forges), ~4 impasses majeures dans l'intégration OpenWebUI**
(PersistentConfig, connexions MCP muettes, téléchargements RAG imposés, session
du mode appel). OpenWebUI est une UI de chat étirée en assistant vocal : pas de
mot d'éveil, micro captif du navigateur, orchestration (historique, injection
mémoire, routage d'outils, personas) enfermée dans ses mécanismes. La recherche
2026 (X-Talk, Audio2Tool) conforte l'architecture **modulaire en cascade** pour
un agent à outils et mémoire — le problème n'est pas la cascade, c'est le
monolithe qui l'orchestre.

## Décision

Sortie **big bang** d'OpenWebUI (interruption de service assumée, sans limite
de durée), remplacé par quatre responsabilités séparées :

1. **Dialogue Forge** (nouveau forge Python, pattern memory-forge) — le
   cerveau : historique de conversation, injection mémoire avant chaque tour et
   extraction après (REST direct vers memory-forge), routage des outils du LLM
   (client MCP vers time/world/pont — les serveurs MCP existants sont
   conservés), personas (prompt + voix), flux LLM phrase par phrase.
2. **Transport voix : Pipecat** — VAD, tours de parole, interruption,
   **mot d'éveil dès la v1** (openWakeWord), streaming STT/TTS. Aucune logique
   métier : il transporte la parole entre la coquille et le Dialogue Forge.
3. **Coquille : application de bureau Tauri (Rust)** — elle est la **carte
   son** de la conversation (micro + haut-parleurs natifs Windows, WebRTC vers
   Pipecat : l'audio de conversation ne traverse plus jamais WSL) et
   l'agrégateur des **modules d'interface, chacun servi par son forge**
   (dialogue par le Dialogue Forge, graphe par memory-forge /viz, voix par
   voice-forge /admin, agenda par time-forge). Pas de SPA monolithique.
4. **Inchangés** : llama.cpp (LLM), whisper.cpp (STT), voice-forge (TTS),
   memory/world/time-forge, Pont hôte (les annonces spontanées continuent de
   sortir par lui, UI fermée comprise), Neo4j. L'embedder reste dans le compose
   (memory-forge en dépend) — modèle porté à Qwen3-Embedding-0.6B GGUF
   (`--pooling last`), le graphe étant vide au moment du swap.

OpenWebUI et son volume sortent du compose ; l'ingestion de documents reste le
watcher de memory-forge ; le RAG-upload-en-chat disparaît sans remplaçant v1.

## Conséquences

- L'orchestration devient du code à nous, testable (TDD, ports/adaptateurs) —
  le pattern qui n'a produit aucune impasse.
- Les pièges OpenWebUI (PersistentConfig, MCP silencieux, session navigateur)
  sortent définitivement du système ; les impasses correspondantes deviennent
  caduques pour la nouvelle stack.
- L'assistant est **muet pendant la reconstruction** (choix assumé) ; l'image
  OpenWebUI reste sur disque comme filet d'urgence.
- `docs/plan-de-tests.md` (écrit le jour même pour la stack OpenWebUI) est
  caduc pour sa partie interface ; les critères d'ACCEPTANCE restent la cible.
- Le mot d'éveil en v1 ajoute un chantier à risque (modèle français,
  faux positifs) au big bang.
- CLAUDE.md, CONTEXT.md et les README doivent être réalignés (fait pour
  CONTEXT.md dans ce commit).

## Alternatives écartées

- **Étranglement progressif (recommandation de l'agent)** : OpenWebUI vidé
  organe par organe, service jamais interrompu. Écarté par l'utilisateur au
  profit de la pureté architecturale.
- **Pipecat comme cerveau** (processeurs custom dans son pipeline) : moins de
  services, mais couple l'orchestration au framework voix.
- **Orchestrateur en Rust** : l'envie Rust est servie par la coquille Tauri ;
  en cerveau, il aurait exigé de réécrire la plomberie temps réel que Pipecat
  fournit, hors des conventions Python éprouvées du dépôt.
- **SPA web unique** : recrée un monolithe frontal ; contredit « un bloc
  spécialisé par service ».
- **Ne remplacer que la couche voix** : laissait deux cerveaux (historique et
  mémoire dans OpenWebUI, voix ailleurs).
