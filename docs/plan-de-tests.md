# Plan de tests d'acceptation — de vive voix (v2)

Réaligné sur la **nouvelle stack modulaire** (ADR 0009, 0010, 0012). L'ancien
plan (mode appel OpenWebUI, Filter et outils collés dans l'UI) est **caduc côté
interface** : ici l'interface est la **coquille** (console + pastille), le temps
réel le **transport voix** (Pipecat), l'orchestration le **Dialogue Forge**.
Référentiels : [ACCEPTANCE.md](ACCEPTANCE.md), [ACCEPTANCE-MEMOIRE.md](ACCEPTANCE-MEMOIRE.md),
[ACCEPTANCE-CAPACITES.md](ACCEPTANCE-CAPACITES.md). Vocabulaire : [CONTEXT.md](../CONTEXT.md).

Ce plan est la procédure que rejouera la **recette finale** (ticket wayfinder
0011) : vraie voix enrôlée, mot d'éveil actif, stack complète.

## Prérequis avant de commencer

- **Forges debout** : `docker compose ps` → tout *healthy* (llm, stt,
  voice-forge, neo4j, embedder, memory, searxng, world, time, dialogue).
- **Pont hôte vivant** : `curl http://127.0.0.1:8500/health` — sinon
  `scripts/demarrage-hote.sh` (répare aussi les montages vides après reboot).
- **Transport voix** lancé en natif Windows (port 8700, `--extra pipecat`,
  `TRANSPORT_VOIX_TRANSPORT_BACKEND=pipecat`).
- **Coquille** lancée sur Windows (`cargo tauri dev`).
- Piège récurrent : après un reboot Windows, les montages `personas/` (service
  `dialogue`) et `voices/` (voice-forge) peuvent être vides → 404/400 silencieux.
  `docker compose up -d --force-recreate dialogue` recharge (un simple `restart`
  ne suffit pas).

Dérouler **dans l'ordre** : chaque étape s'appuie sur la précédente.

## 0. Latence technique (sans micro) — cible ≤ 2 s

```bash
scripts/mesure-latence.sh
```

Mesure la chaîne STT → LLM (première phrase) → TTS et compare à la **cible v2
≤ 2 s** face à la référence historique **2,88 s** (ancienne stack, ACCEPTANCE.md).
Noter la valeur : ______ s. Si dépassé : l'arbitrage est cadré (relâcher la cible
ou TTS streamé, chantier C2 — hors stack qui parle).

## 1. Premier tour de parole (ACCEPTANCE § scénario principal)

Dans la coquille, persona par défaut :

1. Ouvrir la conversation par la **pastille** (bouton — le mot d'éveil est
   différé en v1, ADR 0012). Le WebRTC s'établit à ce moment.
2. **Dire** : « Quelle heure est-il ? » → l'assistant **répond à voix haute** ;
   la première réponse à froid peut être lente (prefill LLM ~13 s la 1ʳᵉ fois,
   ~0,8-1,3 s ensuite — ne pas diagnostiquer une pagination sur ce seul symptôme).
3. **Vérifier** : réponse orale (pas de markdown lu), la phrase s'affiche dans le
   module dialogue **au moment où elle est jouée** (RTVI).

## 2. Multi-tours et fin de conversation (ADR 0012)

1. Sans re-déclencher, enchaîner un 2ᵉ puis 3ᵉ tour (micro ouvert) : les tours
   passent sans nouveau mot d'éveil ni nouveau bouton.
2. **Fin par silence** : se taire au-delà de la fenêtre d'écoute de suite → la
   conversation se **termine**, la pastille repasse en **veille**.
3. **Fin par arrêt explicite** : rouvrir, puis arrêter au bouton (ou phrase de
   fin) → même clôture.
4. **Vérifier la capture mémoire** : chaque clôture déclenche `/clore` (épisode
   *user-only*) — contrôle dans /viz au scénario 4.

## 3. Interruption (ACCEPTANCE § interruption ; preset casque)

1. Preset **casque** (interruption activée). Poser une question dont la réponse
   est longue, puis **couper la parole** à l'assistant.
2. **Vérifier** : l'assistant **se tait** immédiatement.
3. **Tour suivant** : reprendre la conversation → l'assistant **ne référence
   jamais l'inaudible** (troncature `/interrompre` du dernier tour assistant au
   préfixe prononcé). Les phrases non dites ne sont jamais affichées.
4. Preset **haut-parleurs** : rejouer une réponse longue → l'assistant **ne
   s'auto-interrompt pas** en s'entendant.

## 4. Scénario Léa — mémoire ambiante (ACCEPTANCE-MEMOIRE § souvenir)

1. **Dire** : « Ma fille Léa commence le judo mercredi. » Terminer la
   conversation (silence ou arrêt) ; attendre ~30 s (extraction différée à la
   clôture).
2. **Vérifier** dans le module `/viz` (http://127.0.0.1:8200/viz) : entités
   Léa/judo présentes, provenance conversation.
3. **Nouvelle conversation** : « Qu'est-ce que Léa a cette semaine ? » →
   l'assistant répond **judo sans qu'on le lui rappelle** (injection au tour).

## 5. Croisement document (ACCEPTANCE-MEMOIRE § croisement)

1. Créer `documents/judo-club.md` (ré-ingestion automatique ~10 s par le watcher
   de memory-forge) :
   ```markdown
   # Club de judo municipal
   Cours enfants : mercredi 14 h - 15 h 30, dojo du gymnase Jean-Moulin.
   ```
2. **Vérifier** dans /viz : l'entité « judo » relie le souvenir ET le document.
3. **Dire** : « À quelle heure est le judo de Léa ? » → réponse issue du document
   (14 h) sans dicter la source.

## 6. Recall, oubli, obsolescence (ACCEPTANCE-MEMOIRE § recall, § oubli)

1. **Dire** : « Qu'est-ce que je t'ai dit au sujet de Léa ? » → le LLM appelle
   l'outil `recall` (vérifiable : `docker compose logs memory`).
2. **Dire** : « Oublie tout ce que je t'ai dit sur Léa. » → l'assistant annonce
   ce qu'il va oublier avant d'agir ; dans /viz les faits Léa **disparaissent**
   (supprimés, pas invalidés).
3. **Obsolescence** (expérience « déménagement », validée en réel) : un fait
   contredit (« j'ai déménagé à Lyon ») rend l'ancien (« à Paris ») obsolète —
   `invalid_at` posé, mais l'historique reste dans le graphe.

## 7. Persona off-record (ACCEPTANCE-MEMOIRE § off-record)

Conversation avec un persona **off-record** (`personas/`) : après clôture,
**vérifier** qu'aucun nouvel épisode n'apparaît (/viz ni `docker compose logs
memory`).

## 8. Minuteur, rappel, annonce sur enceintes (ACCEPTANCE-CAPACITES)

1. **Dire** : « Mets un minuteur pâtes de 1 minute. » → confirmation orale.
2. Terminer la conversation. À l'échéance : **l'annonce sort sur les enceintes**
   (chaîne Time Forge → Voice Forge → Pont hôte, ADR 0008).
3. **Dire** : « Rappelle-moi demain à 9 h d'appeler le dentiste. » →
   confirmation avec la date en clair ; « Qu'est-ce que j'ai demain ? » →
   l'événement est listé.

## 9. Monde extérieur (ACCEPTANCE-CAPACITES)

1. « C'est quoi la dernière version de Python ? » → 1-2 phrases, **source
   nommée**, jamais de liste de liens.
2. « Quel temps demain à Lyon ? » → lieu, description, min/max.
3. « Fais-moi le briefing » → résumé par source (ou l'assistant dit qu'aucun
   flux n'est configuré ; renseigner `WORLD_FORGE_FEEDS` dans le compose).
4. « Lis-moi cette page : `<adresse>` » → restitution, troncature signalée si longue.

## 10. Actions du catalogue + refus hors liste blanche (ACCEPTANCE-CAPACITES)

Prérequis : Pont hôte avec `catalog.toml` réel et `HOST_BRIDGE_RUNNER=subprocess`
(**jamais exécuté à ce jour** — à valider ici).

1. « Mets pause » → l'assistant retrouve l'action `musique` du catalogue, le Pont
   l'exécute (argv explicite, jamais un shell), confirme oralement.
2. Une demande hors catalogue est **refusée explicitement** sans rien exécuter
   (liste blanche fermée, ADR 0008).

## 11. Vraie voix (ACCEPTANCE § scénario voix)

1. Module `/admin` (http://127.0.0.1:8100/admin) : importer le `speaker.wav` de
   la vraie voix.
2. La choisir dans le persona **et** dans le compose (`TIME_FORGE_ANNOUNCE_VOICE`) ;
   supprimer `VoixDeTest`.
3. Rejouer le smoke-test annonce :
   ```bash
   curl -X POST http://127.0.0.1:8400/announce \
     -H "Content-Type: application/json" -d '{"text":"Essai de la vraie voix."}'
   ```

## Vigilances (docs/impasses.md)

- Toute modification WSL du code transport exige un **redémarrage du process
  Windows** (il lit `\\wsl.localhost`).
- Adaptateurs réels **jamais exécutés à ce jour** : `SubprocessRunner` (Pont
  hôte), `_RealQwen3TTSEngine` (voice-forge), passerelle `RealWorld`, `GraphitiMemory`
  — à qualifier à leur premier usage réel.
- Le fix TTS PCM16 à la source (voice-forge) n'est effectif qu'après rebuild de
  l'image (`docker compose build voice-forge`) ; le normaliseur WAV du transport
  couvre en attendant.
