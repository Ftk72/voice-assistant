---
label: wayfinder:prototype
statut: ouvert
assigne:
bloque-par: []
carte: carte-graphe-memoire
---

# Contrefactuels « et si ? »

## Question

Gradué au grilling du 2026-07-18 (recherche SOTA versée le même jour) :
manipuler le graphe en mode **« et si ? »** — masquer visuellement une entité
ou une arête et voir l'analyse se recalculer (communautés, ponts, trous,
insight), pour comprendre **ce qui tient à quoi** dans la mémoire. Famille de
recherche : perturbation minimale → dérive observée
([CFFTLLMExplainer](https://arxiv.org/abs/2509.21241),
[LLM Analyzer](https://arxiv.org/abs/2405.00708)).

Prototype HITL (/prototype, l'utilisateur juge à l'œil dans `/viz`) :

- **Le geste** : comment on masque (clic sur nœud/arête en mode « et si »,
  panier de masques cumulables, bouton retour au réel ?) — le masque est
  **éphémère et purement visuel/analytique**, jamais écrit en base (la
  correction durable, c'est 0029).
- **Le recalcul** : Louvain, ponts et trous se recalculent côté serveur sur le
  sous-graphe masqué (`analyse.py` prend-il un filtre ?) ; l'insight LLM
  est-il rejoué à chaque masque ou à la demande (9 s en régime — trop lent
  pour du temps réel) ?
- **La lisibilité** : comment montrer *ce qui a changé* (communautés
  re-colorées ? diff avant/après ? les nœuds orphelins créés par le
  masque ?) sans perdre l'utilisateur.

Jouable au navigateur sur le corpus synthétique — indépendant de la séance de
validation (0024). Dernier des trois chantiers du grilling (transparence →
correction → contrefactuels) : le plus spectaculaire, mais valeur à confirmer
au prototype.

## Critère de clôture

Un mode « et si ? » jugé à l'œil par l'utilisateur et livré (ou renoncement
argumenté consigné) — masques éphémères, recalcul serveur, retour au réel
en un geste.
