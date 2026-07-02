# CONTEXT — Assistant vocal local

Glossaire du domaine. Uniquement le vocabulaire — aucun détail d'implémentation.

## Termes

**Assistant vocal** — Le système complet : OpenWebUI (interface + conversations) + moteurs locaux (LLM, STT, TTS). Souverain (voir ce terme).

**Souveraineté** — La contrainte fondatrice du système : les modèles (LLM, STT, TTS) et les données personnelles (mémoire, conversations, agenda) restent en local ; aucun service d'IA cloud. Des requêtes sortantes anonymes (météo, recherche web) sont permises.

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

## Termes — Quotidien (phase 3)

**Annonceur** — Le canal de parole spontanée de l'assistant : il fait entendre une annonce vocale (voix du Voice Forge) sur les enceintes, sans conversation en cours. L'assistant ne parle jamais spontanément autrement.

**Annonce** — Un message parlé par l'annonceur (échéance d'un minuteur, rappel), doublé d'une notification visuelle dans OpenWebUI.

**Rappel** — Un événement d'agenda créé à la voix (« rappelle-moi mercredi de… ») dont la raison d'être est son annonce à l'échéance. Cas particulier d'événement, pas un mécanisme séparé.

**Minuteur** — Un compte à rebours court et éphémère (« mets un minuteur pâtes de 8 minutes »), précis à la seconde, qui produit une annonce à l'échéance. Distinct du rappel : il ne survit pas à son échéance.

## Termes — Actions (phase 4)

**Action** — Une opération sur la machine hôte (ouvrir une application ou un fichier, lancer un script personnel, régler le volume, piloter la musique), déclenchée à la voix. L'assistant ne peut exécuter que des actions du catalogue, jamais une commande arbitraire.

**Catalogue d'actions** — La liste blanche fermée des actions disponibles, définie et nommée à l'avance par l'utilisateur. Extensible sans modifier l'assistant.

**Pont hôte** — Le composant qui donne pied à l'assistant sur la machine hôte, hors des conteneurs : il joue les annonces sur les enceintes et exécute les actions du catalogue. Sans intelligence : il ne décide rien, il exécute.

## Termes — Agenda (phase 5)

**Agenda** — Le calendrier personnel de l'utilisateur, stocké en local (souverain), consultable et modifiable à la voix. Il est l'unique lieu des choses datées : rendez-vous, échéances, rappels.

**Événement** — Une entrée datée de l'agenda. Peut porter une annonce (« préviens-moi une heure avant ») ; le rappel est l'événement dont l'annonce est la raison d'être. Le minuteur, éphémère et précis à la seconde, reste hors agenda.

**Time Forge** — Le composant sur mesure du temps : agenda, minuteurs et annonceur.

## Termes — Monde extérieur (phase 6)

**Réponse sourcée** — La forme unique de la recherche web à la voix : l'assistant cherche, lit les résultats et répond en quelques phrases en citant sa source. Jamais de liste de liens.

**Briefing** — Un résumé parlé de l'actualité, construit à partir de flux choisis par l'utilisateur. Demandable à la voix ou délivré par l'annonceur (ex. briefing du matin).

**Lecture de page** — La restitution vocale (lecture ou résumé) d'une page précise désignée par l'utilisateur.

**World Forge** — Le composant sur mesure de l'accès au monde extérieur, derrière lequel vivent la réponse sourcée, la météo, le briefing et la lecture de page.
