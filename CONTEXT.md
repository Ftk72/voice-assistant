# CONTEXT — Assistant vocal local

Glossaire du domaine. Uniquement le vocabulaire — aucun détail d'implémentation.

## Termes

**Assistant vocal** — Le système complet : la coquille (interface), l'orchestrateur de dialogue et les moteurs locaux (LLM, STT, TTS). Souverain (voir ce terme).

**Souveraineté** — La contrainte fondatrice du système : les modèles (LLM, STT, TTS) et les données personnelles (mémoire, conversations, agenda) restent en local ; aucun service d'IA cloud. Des requêtes sortantes anonymes (météo, recherche web) sont permises.

**Voice Forge** — Le composant sur mesure de la synthèse vocale : API TTS compatible OpenAI et Voice Manager. Consommé par le transport voix et par l'annonceur.

**Voix** — Une identité vocale nommée (ex. « Emma », « Batman »), matérialisée par un échantillon de référence (`speaker.wav`) et ses métadonnées. Sélectionnable instantanément depuis l'interface.

**Persona** — L'association d'un prompt système « voice-first » (réponses orales, courtes, sans mise en forme) et d'une voix par défaut, tenue par l'orchestrateur de dialogue. Ex. : le persona « Batman » parle avec la voix « Batman ».

**Preset audio** — Un des deux réglages d'usage documentés : « casque » (interruption de l'assistant activée) ou « haut-parleurs » (interruption désactivée). Basculable en un clic.

**Voice Manager** — Sous-système du Voice Forge : import, clonage, activation, aperçu et suppression des voix.

**Provider TTS** — Implémentation interchangeable d'un moteur de synthèse derrière `BaseTTSProvider`. Changer de provider ne modifie jamais le reste du système.

**Moteur STT** — Le transcripteur de la parole, servi en local derrière un endpoint compatible `/audio/transcriptions`.

**Conversation** — L'échange vocal continu avec l'assistant : mot d'éveil ou déclenchement manuel, tours de parole détectés, transcription, réponse streamée phrase par phrase, interruption possible de l'assistant. (Remplace le terme « mode appel ».)

## Termes — Architecture modulaire (ADR 0009)

**Orchestrateur de dialogue (Dialogue Forge)** — Le cerveau conversationnel : il tient l'historique, injecte la mémoire avant chaque tour et fait extraire après, route les appels d'outils vers les forges, applique le persona. Aucune interface : il sert le dialogue, la coquille l'affiche.

**Transport voix** — La couche temps réel de la conversation : mot d'éveil, détection de parole, tours, interruption, acheminement de l'audio entre la coquille et les moteurs. Sans logique métier.

**Coquille** — L'application de bureau native de l'assistant : elle est la carte son de la conversation (micro et haut-parleurs) et assemble les modules d'interface. Elle ne contient aucune logique métier.

**Module d'interface** — Une vue de la coquille servie par le forge qui en est propriétaire (dialogue, graphe de mémoire, voix, agenda). Un module évolue avec son forge, jamais avec la coquille.

**Mot d'éveil** — Le déclencheur vocal de la conversation (« dis … »), détecté en continu par le transport voix, sans que rien ne quitte la machine.

## Termes — Mémoire (phase 2)

**Memory Forge** — Le second composant sur mesure : service de mémoire persistante en graphe. Alimente l'assistant en souvenirs et connaissances ; l'orchestrateur de dialogue le consomme (injection et extraction directes, recall/oubli comme outils).

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

**Annonce** — Un message parlé par l'annonceur (échéance d'un minuteur, rappel), doublé d'une notification visuelle dans la coquille.

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
