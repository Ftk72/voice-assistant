# Roadmap — Assistant vocal local

Rédigée le 2026-07-07 à l'issue du grilling UI/fonctions (ADR 0010). Fait
autorité sur l'ordre et le périmètre ; les décisions d'architecture vivent
dans `docs/adr/` (0009 : sortie d'OpenWebUI ; 0010 : UI console + pastille).
Méthode actée : **deux fronts en parallèle** — le chemin critique voix mené
en session, les modules UI sans dépendance délégués (composants disjoints).

État au 2026-07-07 : Dialogue Forge construit, validé en réel et optimisé
(première phrase ~1,2 s à chaud, cache de préfixe llama.cpp maîtrisé, recall
fonctionnel, 24 tests). L'assistant est muet (big bang ADR 0009 en cours).

## Contraintes matérielles transverses (à relire avant chaque chantier)

- **RTX 5080 = 16 Go VRAM, Blackwell sm_120** : aucun binaire CUDA présumé
  compatible sans test réel (CLAUDE.md, docs/impasses.md). Budget VRAM
  actuel : LLM ~6 Go (MoE, experts en RAM) + STT ~1 Go + TTS à venir ; toute
  fonction GPU nouvelle (VLM, empreinte vocale) se paie sur le reliquat ou en
  pagination RAM (64 Go — confortable mais débit divisé).
- **Prefill lent** (experts MoE en RAM CPU) : tout octet instable en amont du
  prompt re-paie du préremplissage — règle « préfixe stable » du Dialogue
  Forge à respecter par toute nouvelle fonction (consignes constantes,
  injection en aval).
- Cibles inchangées (ACCEPTANCE) : voix→voix ≤ 2 s ; référence ancienne
  stack 2,88 s (TTS non streamé = le mur).

---

## Front A — chemin critique : retrouver la voix

### A1. Swap embedder (préalable, bloqué sur téléchargement utilisateur)
bge-m3 → `Qwen/Qwen3-Embedding-0.6B-GGUF` (~640 Mo, l'utilisateur télécharge).
Piège connu : `--pooling last` sur llama-server, sinon embeddings de tokens.
Le graphe est vide (purgé le 2026-07-07) : le swap est gratuit maintenant.

### A2. Transport voix : Pipecat + mot d'éveil
Service Python (conventions forges) : transport SmallWebRTC côté coquille,
VAD, tours de parole, interruption illimitée (choix acté), openWakeWord
(**risque ouvert : modèle français** — repli documenté : bouton d'abord),
STT whisper.cpp existant, TTS voice-forge existant, branché sur le Dialogue
Forge (REST/NDJSON phrase par phrase). Émet les événements RTVI consommés
par le module dialogue (transcriptions, phrases au moment de leur lecture).
- Prémisse à lever tôt : prototype WebRTC WebView2↔Pipecat (jamais testé).

### A3. Coquille Tauri v1 (Rust)
Multi-fenêtres : **console** à onglets (charge les modules servis par les
forges) + **pastille** (état veille/écoute/parle, raccourci global,
notifications d'annonces console fermée). Audio par la webview
(getUserMedia + client Pipecat JS — AEC/NS/AGC Chrome gratuits). Aucune
logique métier : assemblage, fenêtres, tray, raccourcis.

### A4. Module dialogue (servi par le Dialogue Forge)
Page web du forge : encadré de conversation (phrases affichées **au moment
où elles sont prononcées**, via RTVI), menu déroulant **persona** (pilote —
nouveau fil à chaque changement), menu déroulant **voix** (déroge pour la
conversation en cours), historique du fil, indicateur d'outils appelés.
Le Dialogue Forge gagne : endpoint de dérogation de voix, exposition de la
voix courante au transport.

### A5. Retrait d'OpenWebUI du compose
L'image reste sur disque en secours. Les critères ACCEPTANCE se rejouent sur
la nouvelle stack (plan de tests à réécrire — l'ancien est caduc côté
interface).

## Front B — modules UI délégables en parallèle (aucun fichier partagé avec A)

### B1. Graphe mémoire 3D (module `/viz` de memory-forge, refonte)
3d-force-graph (three.js/WebGL, vendoré local), type InfraNodus :
- vue force-directed 3D du graphe entier, orbite/zoom, clic = déplier le
  voisinage (endpoint `/graph` existant) ;
- **extensions REST côté forge** : graphe complet paginé, détection de
  communautés (coloration), centralité (taille des nœuds) ;
- filtres par **provenance** (conversation/document — le glossaire l'exige),
  par date (`valid_at`/`invalid_at` : faits obsolètes estompés, curseur
  temporel « la mémoire telle qu'elle était ») ;
- recherche d'entité, bascule 2D/3D, oubli à la demande depuis la vue
  (DELETE /facts existant).

### B2. Module voix (voice-forge `/admin`, évolution)
Existant à intégrer en onglet. À ajouter : **enrôlement de la vraie voix**
(la VoixDeTest est partout, y compris `TIME_FORGE_ANNOUNCE_VOICE`), aperçu
instantané, presets audio casque/haut-parleurs (bascule interruption).

### B3. Module agenda (time-forge)
Vue agenda/minuteurs servie par time-forge (pattern `/viz`) : événements,
rappels, minuteurs en cours avec compte à rebours visuel.

### B4. Notifications d'annonces dans la coquille
Chaque annonce est doublée d'une notification visuelle (glossaire) : la
pastille les affiche, console fermée comprise. Canal : SSE/WebSocket de
time-forge vers la coquille (à concevoir côté forge).

## Ensuite — par coût croissant (validé au grilling)

### C1. Proactivité (quasi gratuite : annonceur + time-forge existants)
Briefing du matin annoncé à heure fixe (world-forge briefing → voice-forge →
Pont hôte), « rendez-vous dans une heure », météo du jour au réveil, résumé
du soir. Chaque proactivité est un événement time-forge + un gabarit de
message — pas de nouveau service.

### C2. Vraie voix + Qwen3-TTS (chantier TTS)
Enrôlement de la voix personnelle (B2), puis essai de `_RealQwen3TTSEngine`
(**jamais exécuté** ; risques ouverts : sm_120, tokenizer audio du paquet
qwen-tts ; poids déjà sur disque). Objectif latence : TTS streamé par
morceaux pour casser le mur des 1,72 s mesurés sur l'ancienne stack.

### C3. Identification du locuteur
Empreinte vocale locale (ECAPA-TDNN via speechbrain, léger sur GPU) dans le
transport voix : mémoire par personne, réponses personnalisées, **mode invité
off-record automatique** (voix inconnue → rien n'est mémorisé). S'appuie sur
le persona off-record du glossaire.

### C4. Vision d'écran
« Regarde mon écran » : capture par la coquille (Rust, natif Windows), VLM
local (Qwen3-VL quantifié) via un port/adaptateur du Dialogue Forge.
Contrainte dure : 16 Go de VRAM partagés avec le LLM — soit pagination RAM
(lent), soit orchestration exclusive (décharger/recharger), à instruire par
un banc avant tout engagement. Le chantier le plus lourd de la roadmap.

## Idées SOTA en réserve (non engagées — à trier plus tard)

- **Tours de parole sémantiques** (smart turn detection Pipecat) : couper
  quand la phrase est finie, pas quand le silence dure.
- **Consolidation nocturne de la mémoire** : résumé/fusion périodique des
  épisodes en faits durables (tâche time-forge → memory-forge).
- **Rejeu de conversation** : réécouter un échange (audio archivé + texte
  synchronisé) depuis l'historique du module dialogue.
- **HUD de latence** : `scripts/mesure-latence.sh` intégré en overlay dev de
  la console (STT/LLM/TTS par tour).
- **Mot d'éveil entraîné sur mesure** (openWakeWord custom) si le modèle
  français générique déçoit.
- **Mode dictée** : STT continu vers le presse-papier/fichier, sans dialogue.
- **Zoom sémantique du graphe** : agrégation en communautés au dézoom,
  entités au zoom (InfraNodus-like, au-dessus de B1).

## Ce qui est explicitement hors roadmap

- **Domotique / Home Assistant** : écarté au grilling du 2026-07-07 (pas
  d'infrastructure chez l'utilisateur).
- RAG-upload-en-chat : disparu sans remplaçant v1 (ADR 0009) — l'ingestion
  documentaire reste le watcher de memory-forge.
- Tout cloud IA : contrainte fondatrice (souveraineté).
