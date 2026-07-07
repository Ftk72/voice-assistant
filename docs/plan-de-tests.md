# Plan de tests d'acceptation — de vive voix

État de départ (2026-07-07) : graphe mémoire **vierge**, chats OpenWebUI purgés,
STT Whisper sm_120 validé, chaîne d'annonce enceintes validée (smoke-test).
Référentiels : `docs/ACCEPTANCE.md`, `ACCEPTANCE-MEMOIRE.md`, `ACCEPTANCE-CAPACITES.md`.

Dérouler **dans l'ordre** : chaque étape s'appuie sur la précédente. Avant de
commencer : stack healthy (`docker compose ps`) et Pont hôte vivant
(`curl http://127.0.0.1:8500/health`) — sinon `scripts/demarrage-hote.sh`.

## 0. Latence technique (sans micro) — critère n° 1

```bash
scripts/mesure-latence.sh
```

Mesure la chaîne STT → LLM (première phrase) → TTS et compare au budget
**≤ 2 s** (ACCEPTANCE.md). Si ROUGE : options connues — réduire le system
prompt du persona, quantifier le cache KV, streaming TTS par phrase (déjà
actif en mode appel). Noter la valeur ici : ______ s.

## 1. Scénario Léa — mémoire ambiante (ACCEPTANCE-MEMOIRE § souvenir)

En mode appel, persona « assistant » (Filter mémoire + outil memory attachés) :

1. **Dire** : « Ma fille Léa commence le judo mercredi. » Terminer la conversation
   (fermer l'appel), attendre ~30 s (extraction différée).
2. **Vérifier** : http://127.0.0.1:8200/viz → chercher « Léa » → entités
   Léa/judo présentes, provenance conversation.
3. **Nouveau chat**, mode appel : « Qu'est-ce que Léa a cette semaine ? »
   → l'assistant répond **judo sans qu'on le lui rappelle** (injection).
4. Critère : réponse orale naturelle, pas de markdown lu.

## 2. Croisement document (§ croisement)

1. Créer `documents/judo-club.md` (ré-ingestion automatique ~10 s) :
   ```markdown
   # Club de judo municipal
   Cours enfants : mercredi 14 h - 15 h 30, dojo du gymnase Jean-Moulin.
   Prévoir la licence et une tenue propre.
   ```
2. **Vérifier** dans /viz : l'entité « judo » relie le souvenir ET le document.
3. **Dire** : « À quelle heure est le judo de Léa ? » → réponse issue du
   document (14 h) sans dicter la source.

## 3. Recall explicite puis oubli (§ oubli, § recall)

1. **Dire** : « Qu'est-ce que je t'ai dit au sujet de Léa ? » → le LLM appelle
   l'outil `recall` (vérifiable dans les logs `docker compose logs memory`).
2. **Dire** : « Oublie tout ce que je t'ai dit sur Léa. » → l'assistant annonce
   ce qu'il va oublier avant d'agir (description de l'outil `forget`).
3. **Vérifier** dans /viz : les faits Léa ont **disparu** (supprimés, pas
   invalidés).

## 4. Persona off-record (§ off-record) — à créer d'abord

1. Workspace → Models → **+** : cloner les réglages du persona « assistant »
   (même modèle, même prompt) **sans** la Filter mémoire ni aucun outil.
2. Conversation vocale quelconque avec ce persona, puis **vérifier** :
   aucun nouvel épisode dans /viz ni `docker compose logs memory`.

## 5. Minuteur et rappel réels (ACCEPTANCE-CAPACITES § minuteur, § rappel)

Prérequis : outils MCP `time` attachés au persona « assistant »
(éditeur de modèle → Tools ; **pièges connus** — docs/impasses.md : auth
`none`, champ Function Name Filter **vide**, ouvrir un chat **neuf** après).

1. **Dire** : « Mets un minuteur pâtes de 1 minute. » → confirmation orale.
2. Fermer l'appel. À l'échéance : **l'annonce sort sur les enceintes**
   (chaîne Time → Voice Forge → Pont, validée au smoke-test).
3. **Dire** : « Rappelle-moi demain à 9 h d'appeler le dentiste. » →
   confirmation avec la date en clair ; « Qu'est-ce que j'ai demain ? » →
   l'événement est listé.

## 6. Monde extérieur (§ sourcée, § météo, § briefing, § lecture)

Prérequis : outils MCP `world` attachés (mêmes pièges) ; pour le briefing,
renseigner `WORLD_FORGE_FEEDS` dans le compose (flux RSS séparés par des
virgules) puis `docker compose up -d world`.

1. « C'est quoi la dernière version de Python ? » → 1-2 phrases, **source
   nommée**, jamais de liste de liens.
2. « Quel temps demain à Lyon ? » → lieu, description, min/max.
3. « Fais-moi le briefing » → résumé par source (ou l'assistant dit qu'aucun
   flux n'est configuré).
4. « Lis-moi cette page : <url> » → restitution, troncature signalée si longue.

## 7. Presets audio (ACCEPTANCE § scénario principal, point 5)

1. **Casque** : Settings → Audio → activer *Allow Voice Interruption in Call* ;
   couper la parole à l'assistant → il s'arrête.
2. **Haut-parleurs** : désactiver le même réglage ; vérifier qu'il ne
   s'auto-interrompt pas.

## 8. Vraie voix (ACCEPTANCE § scénario voix) — quand tu es prêt

1. http://127.0.0.1:8100/admin : importer `speaker.wav` de la vraie voix.
2. La choisir dans le persona (TTS Voice) **et** dans le compose
   (`TIME_FORGE_ANNOUNCE_VOICE`) ; supprimer VoixDeTest.
3. Rejouer le smoke-test annonce : `curl -X POST http://127.0.0.1:8400/announce
   -H "Content-Type: application/json" -d '{"text":"Essai de la vraie voix."}'`

## Hors périmètre immédiat (chantiers ouverts)

- Actions du catalogue : écrire `catalog.toml` (réel), relancer le Pont avec
  `HOST_BRIDGE_RUNNER=subprocess`, brancher `http://host.docker.internal:8500/mcp`
  dans OpenWebUI — puis tester « mets pause » et le refus hors liste blanche.
- Extraction 4/5 → 5/5, dédoublonnage des épisodes (hérités du handoff 0009).
