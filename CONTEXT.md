# CONTEXT — Assistant vocal local

Glossaire du domaine. Uniquement le vocabulaire — aucun détail d'implémentation.

## Termes

**Assistant vocal** — Le système complet : OpenWebUI (interface + conversations) + moteurs locaux (LLM, STT, TTS). Entièrement local, aucun cloud.

**Voice Forge** — Le seul composant développé sur mesure : backend FastAPI exposant une API TTS compatible OpenAI et le Voice Manager. OpenWebUI le consomme comme un fournisseur TTS externe.

**Voix** — Une identité vocale nommée (ex. « Emma », « Batman »), matérialisée par un échantillon de référence (`speaker.wav`) et ses métadonnées. Sélectionnable instantanément depuis OpenWebUI.

**Persona** — Un modèle OpenWebUI (au sens `model.info.meta`) associant un prompt système « voice-first » (réponses orales, courtes, sans mise en forme) et une voix par défaut (`meta.tts.voice`). Ex. : le persona « Batman » parle avec la voix « Batman ».

**Preset audio** — Un des deux réglages d'usage documentés : « casque » (interruption de l'assistant activée) ou « haut-parleurs » (interruption désactivée). Réglage natif OpenWebUI, basculable en un clic.

**Voice Manager** — Sous-système du Voice Forge : import, clonage, activation, aperçu et suppression des voix.

**Provider TTS** — Implémentation interchangeable d'un moteur de synthèse derrière `BaseTTSProvider`. Changer de provider ne modifie jamais OpenWebUI.

**Moteur STT** — Voxtral Mini, servi en local, consommé par OpenWebUI via son moteur STT « openai » (endpoint compatible `/audio/transcriptions`).

**Mode appel** — La conversation vocale continue native d'OpenWebUI (CallOverlay) : VAD, transcription, synthèse en streaming, interruption de l'assistant.

## Termes — Mémoire (phase 2)

**Memory Forge** — Le second composant sur mesure : service de mémoire persistante en graphe. Alimente l'assistant en souvenirs et connaissances ; OpenWebUI le consomme via ses mécanismes natifs (Filter, MCP).

**Entité** — Un nœud nommé du graphe (personne, lieu, projet…). Une même entité relie les faits issus des conversations et ceux issus des documents.

**Fait** — Une relation entre entités, portant sa provenance et sa période de validité. Un fait contredit devient obsolète : il cesse d'être utilisé mais reste dans l'historique du graphe.

**Épisode** — L'unité d'ingestion de la mémoire : un échange de conversation daté, ou un fragment de document.

**Provenance** — L'origine d'un fait : conversation (datée) ou document (nommé). Toujours conservée, filtrable dans la visualisation.

**Injection** — L'apport ambiant de faits pertinents dans le contexte du LLM avant chaque génération, sans intervention de l'utilisateur.

**Recall** — L'interrogation explicite de la mémoire par le LLM (« qu'est-ce que je t'ai dit sur X ? »), via un outil.

**Oubli** — La suppression réelle et définitive de faits à la demande de l'utilisateur (distincte de l'obsolescence, qui conserve l'historique).

**Persona off-record** — Un persona dont les conversations ne sont jamais mémorisées.
