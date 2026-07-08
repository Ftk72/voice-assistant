# Handoff 0012 — Politique de mémoire actée (ADR 0011), ontologie à 8 types, capture par conversation

> Convention : handoffs versionnés dans `docs/handoffs/`, seul le plus récent
> fait foi. En fin de session, générer le 0013 via `/handoff`.

Date : 2026-07-08 · Remplace le 0011. Session couverte : **grilling « que
mémorise-t-on ? »** (le point ouvert laissé par le 0011 après la purge du
graphe), gravé en **ADR 0011** ; puis deux lots d'implémentation en TDD
(ontologie étendue côté memory-forge, capture par conversation côté
dialogue-forge). **Rien n'est commité** — l'arbre porte toute la session ;
trois commandes de commit prêtes (voir plus bas).

## Lire avant tout (fait autorité)

- `docs/adr/0011-politique-de-memoire-de-conversation.md` — **LE document né de
  la session** : 10 décisions sur ce qu'on mémorise, de qui, sous quelles
  conditions. Ne pas rediscuter sans nouveau grilling. Précise l'ADR 0005
  (Graphiti) et l'ADR 0009.
- `CONTEXT.md` — glossaire mémoire mis à jour : *Épisode* (tours utilisateur
  d'une conversation, capturés à la fermeture, zéro en off-record), *Provenance*
  (conversation datée, pas le persona), *Entité* (8 catégories déclarées).
- `docs/roadmap.md` + `docs/adr/0010-…` — pilotage inchangé (deux fronts A/B).

## Ce qui a été fait cette session (détail dans l'ADR / le diff, pas ici)

1. **ADR 0011 rédigé** — synthèse du grilling. Points structurants : l'assistant
   **ne fait jamais foi** (cause racine du faux fait corrigée) ; capture **par
   conversation** à la fermeture (la conversation en cours vit déjà dans le
   contexte LLM) ; filtre par **ontologie** plutôt que juge LLM ; frontière
   mémoire/agenda **par nature** (durable au graphe, ponctuel-à-échéance à
   l'agenda) ; extraction **silencieuse** ; réparation par obsolescence Graphiti
   + oubli + audit `/viz`.
2. **memory-forge — ontologie à 8 types** (`app/graph/ontologie.py`,
   `tests/test_ontologie.py`) : ajout `Organisation`, `Animal`, `Bien`,
   `Projet`, `Aliment` aux 3 existants. Bornes testées (test de durée pour
   `Bien`, absence d'échéance pour `Projet`, allergies pour `Aliment`).
   **Vérifié : 70 tests verts, ruff propre.**
3. **dialogue-forge — capture par conversation** (`personas.py`, `dialogue.py`,
   `routes/api.py`, `memoire/base.py`, 3 fichiers de tests) : `Persona.off_record`
   (jeton `, off-record` dans le titre) ; `Orchestrateur.clore_conversation()`
   (épisode user-only, exclut contexte mémoire + backchannels, skip off-record) ;
   **capture per-tour supprimée** ; route `POST /conversations/{id}/clore`.
   **Vérifié : 33 tests verts (dont invariants préfixe-cache), ruff propre.**

## État réel constaté

- Les deux composants restent **verts et ruff-propres** après modifs
  (vérifiés à la main cette session, pas seulement déclarés).
- La capture user-only n'a tourné **que contre la mémoire factice** — jamais
  contre memory-forge réel → Graphiti. Le port `capturer_episode(contenu, nom)`
  n'a pas changé de signature : l'adaptateur réel `MemoireREST` est conforme
  sans modification, il sera juste appelé une fois par conversation.
- Le déclencheur de fermeture est **manuel** (`POST /clore`) : le branchement
  automatique à la mise en veille dépend du **front A2** (transport voix).
- Aucun persona `off-record` n'existe encore dans `personas/` (donnée
  utilisateur, à créer au besoin).
- Le graphe Neo4j est toujours **quasi vierge** (purgé au 0011) ; l'image
  memory Docker n'est **toujours pas rebuildée** (le `/viz` 3D n'est pas encore
  servi par le conteneur).

## Rien n'est commité — trois lots prêts (l'utilisateur commite)

Les commandes de commit complètes (git add ciblé + message enveloppant) ont été
fournies dans la conversation pour chacun des trois lots :
1. ADR 0011 + ontologie (docs/adr/0011… + memory-forge 2 fichiers).
2. CONTEXT.md (glossaire mémoire).
3. dialogue-forge (capture par conversation, 7 fichiers).
`host-bridge/catalog.toml` (non suivi) est **hors** de ces lots — ne pas
l'inclure sans savoir ce que c'est.

## Fronts de la roadmap — où on en est

- **Front A (voix)** : A1 embedder FAIT (0011). **A2 (Pipecat + mot d'éveil)
  reste le prochain gros chantier** — il fournira le déclencheur de fermeture
  de conversation qui active la capture automatique. Prémisse à lever tôt :
  prototype WebRTC WebView2↔Pipecat (jamais testé). A3/A4/A5 non commencés.
- **Front B (modules UI)** : B1 graphe 3D FAIT (0011), reste le rebuild image
  memory. B2/B3/B4 non commencés.
- **Chantier mémoire réelle** : la politique est actée (ADR 0011) et
  partiellement implémentée. Reste à **valider en réel** avant de brancher des
  épisodes de prod (cf. prémisses).

## Prémisses à lever (vérifier, pas croire)

- **Obsolescence Graphiti (n°1 du filet de réparation)** : jamais validée en
  réel. Expérience « déménagement » à une heure : « j'habite Paris » puis, autre
  conversation, « j'ai déménagé à Lyon » → l'arête Paris passe-t-elle bien
  `invalid_at` ? Décisif pour tenir (6A) plutôt que le garde-fou (6B).
- Extraction des **8 types** sur épisode réel Graphiti (les nouveaux types
  n'ont jamais vu le prompt d'extraction du 35B) ; en particulier `Aliment`
  pour les allergies (fort enjeu, cf. (5C) en réserve).
- `clore_conversation` bout à bout contre memory-forge réel (fake seulement).
- Héritées du 0011 : `_RealQwen3TTSEngine` jamais exécuté ; mot d'éveil français
  (openWakeWord) ; WebRTC WebView2↔Pipecat ; vraie voix non enrôlée ;
  `GraphitiMemory.graphe_complet` (Cypher) jamais exécutée ; image memory pas
  rebuildée.

## Pièges et acquis (au-delà du registre)

- **Préfixe stable = loi** (rappel 0011) : la capture par conversation ne touche
  pas la construction des messages ; les tests d'invariant préfixe-cache sont
  restés verts, ne pas les casser.
- **Un épisode = tours utilisateur only** : ne jamais réintroduire la parole de
  l'assistant dans un épisode (c'est la cause racine du faux fait).
- **Bancs réels = mémoire factice** (leçon de la pollution du graphe, tient
  toujours).
- `/delegate` bien évalué cette session : les deux lots étaient des cas
  « ne délègue pas » (≤ quelques fichiers, contexte frais, zone sensible) —
  faits inline. Ne pas déléguer par réflexe.

## Méthode de travail (inchangée — CLAUDE.md)

Analyser → proposer → attendre validation → TDD → doc. Tout en français.
Jamais de `git commit` par l'agent ; « texte du commit » = commande git
complète. Gros téléchargements lancés par l'utilisateur. Délégations : brief
autoportant, vérification finale par l'agent principal.

## Suggested skills

- `/premisses` — en ouverture : l'utilisateur a-t-il commité les trois lots ?
  l'obsolescence Graphiti a-t-elle été testée ? l'image memory rebuildée ?
- `/impasses` — consulter avant tout diagnostic ; capturer à chaud.
- `/grilling` — avant le front A2 (API Pipecat↔Dialogue Forge, sémantique
  exacte de « fin de conversation » qui déclenche `/clore`).
- `/tdd` — tout nouveau composant (transport voix) comme dialogue/memory-forge.
- `/delegate` — mais **évaluer d'abord** (étape 1) : cette session a montré que
  les petits lots contextuels se font mieux inline.
- `/handoff` — générer le 0013 en fin de session.
