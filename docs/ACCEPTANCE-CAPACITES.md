# Critères d'acceptation — Capacités (phases 3, 4, 5, 6)

Issus de la session de grilling du 2026-07-02, réalignés sur la stack modulaire
(ADR 0009) : l'orchestration (routage des outils MCP, personas) est tenue par le
**Dialogue Forge**, l'interface par la **coquille** — plus d'OpenWebUI (abandonné,
ADR 0009). Vocabulaire : voir CONTEXT.md (§ Quotidien, Actions, Agenda, Monde
extérieur). Décisions : ADR 0007 (souveraineté), ADR 0008 (Pont hôte). Tout est
jugé **à l'oral** : réponses courtes, sans markdown lu à voix haute, sans liste
de liens.

## Scénario réponse sourcée

1. Je demande « c'est quoi la dernière version de Python ? ».
2. L'assistant cherche (World Forge → SearXNG), lit les extraits et répond en **1-2 phrases en citant sa source** (ex. « D'après la doc officielle, la dernière version stable est Python 3.13. »).
3. Jamais de liste de liens : la source est nommée, pas énumérée.

## Scénario météo

1. « Quel temps demain à Lyon ? ».
2. Réponse parlable issue d'Open-Meteo (API anonyme, sans clé) : lieu, description WMO en français, températures min/max, éventuellement la probabilité de pluie.

## Scénario briefing

1. « Fais-moi le briefing » (ou délivré par l'annonceur le matin).
2. Résumé parlé de l'actualité construit à partir des flux RSS configurés (`WORLD_FORGE_FEEDS`), regroupé par source. Sans flux configuré, l'assistant le dit.

## Scénario lecture de page

1. Je désigne une page (« lis-moi cette page : … »).
2. L'assistant restitue le texte lisible (lecture ou résumé) ; si la page est longue, il signale la troncature.

## Scénario rappel + annonce sur les enceintes

1. « Rappelle-moi mercredi à 15 h d'appeler le dentiste » → le Time Forge crée un événement (rappel = annonce à l'heure dite) et confirme la date en clair.
2. À l'échéance, sans conversation en cours, l'annonce est **synthétisée par le Voice Forge** (voix de l'assistant) puis **jouée sur les enceintes via le Pont hôte** (ADR 0008), doublée d'une notification visuelle dans la coquille (la pastille, console fermée comprise — ADR 0010).

## Scénario minuteur

1. « Mets un minuteur pâtes de 8 minutes » → minuteur `pâtes`, 480 s.
2. L'échéance est **précise à la seconde** (tâche asyncio dédiée, pas de polling) ; l'annonce part au moment dit sur les enceintes.
3. « Il reste combien ? » liste le temps restant ; le minuteur ne survit pas à son échéance.

## Scénario consultation d'agenda

1. « Qu'est-ce que j'ai demain ? » → l'assistant liste les événements du jour demandé (sans lire les identifiants sauf pour une suppression).
2. Sans rien à cette période, il le dit.

## Scénario action du catalogue + refus hors liste blanche

1. « Mets pause » → l'assistant retrouve l'action `musique` dans le catalogue, le Pont hôte l'exécute (argv explicite, jamais un shell), et l'assistant confirme oralement ce qui a été lancé.
2. Une demande qui ne correspond à **aucune action du catalogue** est **refusée explicitement** (« ce n'est pas dans la liste blanche ») **sans rien exécuter** : le catalogue est fermé (ADR 0008).

## Smoke-test annonce

1. `POST /announce` sur le Time Forge (`{"text": "Essai des enceintes."}`) déclenche immédiatement la chaîne annonceur (Voice Forge → Pont hôte) sans attendre une échéance — vérification de bout en bout du son sur les enceintes.

## Exigences transverses

- **Souveraineté** (ADR 0007) : aucune donnée de la mémoire, des conversations ou de l'agenda ne sort ; seuls les termes de la question courante partent vers SearXNG/Open-Meteo/flux.
- **Un seul pied hors Docker** (ADR 0008) : le Pont hôte, sans intelligence — il reçoit du wav prêt à jouer et n'exécute que la liste blanche. Le TTS reste centralisé dans le Voice Forge.
- **Liste blanche fermée** : l'assistant n'a jamais accès à un shell ni à une commande arbitraire.
- **100 % local, ports liés à 127.0.0.1** ; le Pont hôte, joignable via `host.docker.internal:8500`, écoute `0.0.0.0` en usage réel derrière un pare-feu limité au réseau Docker.
- **Serveurs MCP** consommés par le client MCP du Dialogue Forge (`DIALOGUE_FORGE_MCP_URLS`) : `http://world:8300/mcp`, `http://time:8400/mcp`, `http://host.docker.internal:8500/mcp`.
