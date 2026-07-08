# ADR 0012 — Transport voix : cycle de conversation, interruption, contrat Dialogue Forge

Date : 2026-07-08 · Statut : accepté · Précise l'ADR 0009 (architecture modulaire) et l'ADR 0010 (UI/audio par la webview) ; s'appuie sur l'ADR 0011 (politique de mémoire)

## Contexte

Front A2 de la roadmap : le **transport voix** (Pipecat) est le prochain gros
chantier — la couche temps réel qui relie la coquille (micro/haut-parleurs) aux
moteurs (STT whisper.cpp, TTS voice-forge) et à l'orchestrateur (Dialogue Forge,
REST/NDJSON phrase par phrase). L'ADR 0010 a déjà acté que **l'audio passe par
la webview** (getUserMedia + client Pipecat JS → WebRTC vers Pipecat, AEC/NS/AGC
Chrome gratuits) et que **le texte suit la voix** via RTVI. Restaient ouverts :
les bornes d'une conversation, le sort du mot d'éveil, la cohérence après
interruption, la fixité du persona, l'acheminement de la voix.

Audit des prémisses (2026-07-08) : STT et TTS sont des endpoints **OpenAI-compat
vérifiés** (whisper.cpp `/v1/audio/transcriptions` batch, voice-forge
`/audio/speech`) ; `pipecat-ai` 1.5.0 existe (extras `webrtc`/`silero`/`openai`,
py≥3.11) ; les anciennes impasses STT Voxtral sont **caduques** (swap whisper).
Trois différées demeurent : import exact `SmallWebRTCTransport`/RTVI, modèle
mot d'éveil **français**, et le **pont WebRTC WebView2↔Pipecat jamais
prototypé**.

## Décisions

1. **Cycle de conversation : micro ouvert, fin par silence ou arrêt explicite.**
   Une conversation s'ouvre au mot d'éveil ou au bouton, puis enchaîne
   **plusieurs tours micro ouvert** — le mot d'éveil ne re-filtre pas chaque
   tour. Après une réponse de l'assistant, une **fenêtre d'écoute de suite**
   (délai N) garde la conversation ouverte : si l'utilisateur reparle, elle
   continue ; si le silence dépasse N, ou sur arrêt explicite (bouton, phrase de
   fin), elle se **termine** → appel `/clore` (capture mémoire, ADR 0011) →
   veille.

2. **Bouton d'abord ; mot d'éveil différé, navigateur-side quand il viendra.**
   La V1 du transport s'ouvre en **appui manuel** (pastille) : le WebRTC
   s'établit à ce moment. Cela **dé-risque** le chemin critique — valider le
   pont WebView2↔Pipecat (jamais prototypé) avec **un seul inconnu à la fois**,
   avant d'empiler le mot d'éveil. Quand le mot d'éveil sera ajouté, il tournera
   **dans le navigateur** (l'audio ne quitte pas la webview en veille ; « rien
   ne quitte la machine » poussé au processus), pas côté serveur.

3. **Interruption : l'historique ne retient que ce qui a été prononcé.** Sur
   interruption (illimitée, ADR 0010 ; active en preset casque), le transport —
   qui sait combien de phrases il a jouées — signale au Dialogue Forge le
   préfixe réellement dit, et le DF **tronque son dernier tour assistant** à ce
   préfixe. Le LLM ne référence jamais l'inaudible au tour suivant. La
   **mémoire est immunisée** de toute façon (épisode *user-only*, ADR 0011) :
   l'enjeu est la cohérence *live*, pas le graphe.

4. **Persona figé pour la durée de la conversation vocale.** Le persona est
   choisi à l'ouverture et ne change pas en cours ; en changer **termine** la
   conversation (→ `/clore`) et en ouvre une neuve. Le menu persona de la
   console ne s'utilise qu'hors conversation active. Modèle 1:1 : une session
   vocale ↦ une Conversation ↦ un persona ↦ un épisode. Cohérent avec « changer
   de persona = nouvelle conversation » (ADR 0010, glossaire *Persona*).

5. **La voix voyage dans le stream `/tours` ; dérogation effective au tour
   suivant.** Le Dialogue Forge reste la **source unique** persona+voix
   (ADR 0010) : il annote chaque tour du NDJSON avec la voix courante, que le
   transport applique au TTS de ce tour. Une dérogation de voix prend effet au
   **tour suivant** (un tour se synthétise d'un tenant) — perçu comme immédiat
   vu la rapidité des tours. Aucun aller-retour supplémentaire : la voix rid le
   flux déjà consommé.

## Conséquences

- **Nouveau composant `transport-voix/`** aux conventions forges (ADR 0009,
  modèle memory-forge) : `create_app` + `/health`, **ports** STT / TTS /
  Dialogue Forge avec **adaptateurs factices par défaut** (tests, zéro
  réseau/matériel) et un adaptateur **Pipecat réel « jamais exécuté à ce jour »**
  tant qu'il n'a pas tourné. Pipecat en **extra optionnel** (`uv sync --extra
  pipecat`) — aucun téléchargement lourd sans accord, lancé par l'utilisateur.
  Le transport ne sert **aucune UI** (le module dialogue est servi par le DF,
  front A4).
- **Contrat Dialogue Forge à étendre** (lot dialogue-forge) :
  - `POST /conversations/{id}/interrompre` — tronque le dernier tour assistant
    au préfixe prononcé (décision 3) ;
  - le stream `/tours` **porte la voix courante** (décision 5) ;
  - `/clore` — **déjà livré** (ADR 0011, cette session).
- **STT batch = transcription utilisateur affichée après le tour** (whisper.cpp
  n'a pas de partiel) ; les phrases de l'assistant s'affichent à leur lecture
  (ADR 0010). Le transport émet les événements RTVI correspondants.
- **Glossaire** (CONTEXT.md) : *Conversation* précisée (multi-tours, fin par
  silence/explicite, déclenche la capture), *Fenêtre d'écoute de suite* ajoutée.
- **Différées à lever au premier end-to-end** (aucune ne bloque le squelette) :
  import `SmallWebRTCTransport`/RTVI de Pipecat 1.5 ; **pont WebView2↔Pipecat** ;
  modèle mot d'éveil français (lot ultérieur, décision 2).

## Alternatives écartées

- **Fin de conversation explicite seulement** (pas de retombée par silence) :
  micro ouvert sans fin, capture mémoire jamais déclenchée, souveraineté
  ressentie dégradée.
- **Un tour par éveil** (façon enceinte grand public) : contredit le modèle
  multi-tours de l'utilisateur et re-paie le prefill LLM à chaque phrase.
- **Mot d'éveil dès la V1** (côté serveur ou navigateur) : empile deux inconnus
  (wake-word français *et* pont WebRTC) sur le chemin critique ; le repli
  « bouton d'abord » était déjà acté (roadmap).
- **Mot d'éveil côté serveur** (à terme) : micro streamé en continu vers le
  serveur, WebRTC ouvert 24/7 — moins souverain que la détection navigateur.
- **Réponse entière conservée malgré l'interruption** : le LLM référence
  l'inaudible (« comme je disais… ») ; pragmatique mais dégrade la cohérence,
  alors que l'interruption est fréquente *par design*.
- **Jeter le tour assistant interrompu** : efface aussi le début entendu et
  produit deux tours utilisateur d'affilée.
- **Persona changeable en plein vol** : plusieurs threads/épisodes dans une même
  session audio, état retors dans le transport, pour un confort rare en vocal.
- **Voix poussée par la coquille au transport** : logique métier dans la coquille
  (tension ADR 0009), deux sources de vérité pour la voix.
- **Endpoint DF « voix courante » interrogé par tour** : un aller-retour de plus
  quand le stream peut porter l'info gratuitement.
