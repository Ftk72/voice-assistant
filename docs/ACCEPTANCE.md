# Critères d'acceptation — Assistant vocal local (v2)

Recette de la **nouvelle stack modulaire** (ADR 0009, 0010, 0012) : coquille
Tauri + pastille, transport voix Pipecat, Orchestrateur de dialogue, forges.
L'ancienne recette (interface OpenWebUI) est **caduque côté interface**
(ADR 0009) ; ce document est la spec que rejouera la recette finale (ticket
wayfinder 0011). Vocabulaire : [CONTEXT.md](../CONTEXT.md) fait foi.

Les capacités des phases 2 à 6 gardent leurs propres critères, réalignés eux
aussi : [ACCEPTANCE-MEMOIRE.md](ACCEPTANCE-MEMOIRE.md) (mémoire) et
[ACCEPTANCE-CAPACITES.md](ACCEPTANCE-CAPACITES.md) (quotidien, actions, agenda,
monde extérieur).

## Références historiques de latence (ancienne stack)

L'ancienne stack a été **validée de bout en bout le 2026-07-07** ; ses mesures
sont conservées comme **repères historiques**, pas comme mesures de la nouvelle
stack (jamais encore mesurée bout-en-bout) :

| Métrique | Référence ancienne stack (2026-07-07) |
| --- | --- |
| Latence voix → voix (fin de parole → début de réponse audio) | **2,88 s** |
| STT (transcription) | **0,15 – 0,5 s** |
| TTS (synthèse, non streamé — le mur) | **~2 s** (1,72 s mesuré) |
| LLM (débit) | **~33 tok/s** |

**Cibles v2, exprimées relativement à ces repères** :

- **Voix → voix ≤ 2 s** (mieux que la référence 2,88 s ; cf. carte wayfinder).
  Le mur connu est le TTS non streamé (1,72 s) : si la mesure réelle dépasse la
  cible, l'arbitrage est déjà cadré (relâcher la cible ou engager le TTS streamé
  — hors périmètre de la stack qui parle, chantier C2 de la roadmap).
- STT et LLM : **ne pas régresser** sous les repères ci-dessus (même moteurs).

Les valeurs réelles se consignent au procès-verbal de la recette finale
(ticket 0011), critère par critère, face à ces repères.

## Scénario principal — cycle de conversation (ADR 0012)

1. **Ouverture** : la conversation s'ouvre au **mot d'éveil** français
   (« dis … », détecté dans la webview) **ou** par la **pastille** (déclenchement
   manuel). En v1, le mot d'éveil est différé : l'ouverture se fait au bouton de
   la pastille (« bouton d'abord », ADR 0012) ; le mot d'éveil s'ajoute ensuite.
2. **Multi-tours micro ouvert** : après ouverture, plusieurs tours s'enchaînent
   sans re-filtrer par le mot d'éveil. Je pose une question en français,
   naturellement ; la transcription (whisper.cpp, français) est fidèle.
3. **Réponse** : la réponse audio démarre dans la **cible ≤ 2 s** après ma fin
   de phrase, avec la voix courante du persona. Elle est **orale par nature** :
   pas de markdown lu à voix haute, pas d'énumérations mécaniques. Le texte
   **suit la voix** — chaque phrase s'affiche dans le module dialogue au moment
   où sa synthèse commence à être jouée (RTVI, ADR 0010).
4. **Fenêtre d'écoute de suite** : après la réponse, la conversation reste
   ouverte micro ouvert un délai N ; si je reparle, elle continue.
5. **Fin par silence** : si le silence dépasse N, la conversation se **termine**
   et l'assistant retombe en veille (pastille : veille).
6. **Fin par arrêt explicite** : bouton ou phrase de fin termine aussi la
   conversation.
7. **Capture mémoire à la clôture** : toute fin de conversation déclenche
   `/clore` → capture de l'épisode (tours **utilisateur uniquement**, ADR 0011).
   Détails et injection au tour suivant : [ACCEPTANCE-MEMOIRE.md](ACCEPTANCE-MEMOIRE.md).

## Scénario interruption (preset casque, ADR 0012)

1. En preset **casque** (interruption activée), l'assistant parle ; je prends la
   parole par-dessus.
2. L'assistant **se tait immédiatement**.
3. **Cohérence au tour suivant** : l'assistant ne référence **jamais l'inaudible**
   (« comme je disais… » sur une phrase jamais prononcée). Le transport signale
   au Dialogue Forge le préfixe réellement dit ; le DF **tronque son dernier tour
   assistant** à ce préfixe (`/interrompre`). Les phrases jamais prononcées ne
   s'affichent jamais dans le module dialogue.
4. En preset **haut-parleurs** (interruption désactivée), l'assistant ne se coupe
   pas en s'entendant lui-même.

## Scénario voix (CONTEXT.md § Voix)

1. Je dépose un dossier `voices/Emma/` avec un `speaker.wav` de quelques secondes,
   **ou** je l'importe via le module d'interface `/admin` de voice-forge.
2. Sans redémarrer quoi que ce soit, « Emma » apparaît comme voix disponible
   (module `/admin` et sélection de voix par persona).
3. Un aperçu est écoutable depuis `/admin`.
4. **Persona pilote, voix déroge** (ADR 0010) : choisir un persona sélectionne sa
   voix par défaut et **change de conversation** ; changer de voix est instantané
   (effectif au tour suivant, ADR 0012) sans changer de conversation ni de persona.

## Exigences transverses

- **Cycle de conversation complet** : ouverture (mot d'éveil ou pastille),
  multi-tours micro ouvert, fin par silence **et** par arrêt explicite, capture
  mémoire à la clôture — tous vérifiés.
- **Réponses orales** : jamais de markdown, listes ou URL lus à voix haute.
- **Presets audio** (CONTEXT.md § Preset audio) : casque / haut-parleurs,
  basculables en un clic.
- **Souveraineté** (ADR 0007) : aucun appel réseau sortant à l'exécution hors
  requêtes anonymes du World Forge.
- **Sécurité** : ports Docker liés à `127.0.0.1` ; l'audio de conversation passe
  par la coquille en WebRTC local (ne traverse jamais WSL) ; seules les annonces
  sortent par le Pont hôte.
- **VRAM** : les modèles (LLM ~6 Go + STT ~1 Go + TTS ~3 Go) coexistent dans les
  16 Go de la RTX 5080 (ADR 0004), experts MoE du LLM déchargés en RAM.
