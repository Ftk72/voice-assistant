# Critères d'acceptation — Mémoire persistante (phase 2)

Issus de la session de grilling du 2026-07-02 (14 questions). Vocabulaire : voir CONTEXT.md § Mémoire.

## Scénario souvenir (le scénario « Léa »)

1. Lundi, en mode appel, je dis : « ma fille Léa commence le judo mercredi ».
2. La conversation terminée, l'extraction différée peuple le graphe (entités Léa/judo, fait daté, provenance conversation).
3. Mardi, je demande « qu'est-ce que Léa a cette semaine ? » : l'assistant répond judo, **sans que je le lui rappelle** (injection).
4. Un mois plus tard je dis « Léa a arrêté le judo » : le fait initial devient obsolète. L'assistant n'évoque plus le judo au présent, mais l'historique reste visible dans le graphe.

## Scénario croisement (la valeur du graphe unique)

1. Je dépose `documents/judo-club.md` (horaires du club).
2. Après ingestion, l'entité « judo » relie le souvenir conversationnel ET le document.
3. « À quelle heure est le judo de Léa ? » → réponse issue du document, liée par le graphe.

## Scénario oubli et off-record

1. « Oublie tout ce que je t'ai dit sur X » → les faits sont **supprimés** du graphe (pas invalidés), vérifiable dans la visualisation.
2. Une conversation avec le persona off-record ne produit aucun épisode ni fait.

## Scénario recall explicite

1. « Qu'est-ce que je t'ai dit au sujet de mon travail le mois dernier ? » → le LLM interroge la mémoire (outil MCP) et répond avec les faits datés, y compris ceux que l'injection ambiante n'aurait pas ramenés.

## Scénario visualisation

1. Dans la visualisation, je cherche « Léa » : je vois son voisinage, j'étends de proche en proche, je filtre par provenance (souvenir/document) et par validité (actifs/obsolètes).
2. Dès la phase 1 : Neo4j Browser. En phase finale : mini-page custom du Memory Forge.

## Exigences transverses

- **Latence** : l'injection ajoute ≤ 300 ms au chemin fin de parole → début de réponse (budget total ≤ 2 s inchangé).
- **Aucune extraction pendant une conversation vocale** : les jobs 35B attendent la fin de conversation.
- **VRAM** : zéro consommation supplémentaire (extraction = LLM existant, embeddings sur CPU).
- **100 % local, zéro fork** : Filter + MCP natifs côté OpenWebUI ; Neo4j, embedder et Memory Forge liés à 127.0.0.1.
