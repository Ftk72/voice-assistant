# ADR 0007 — Souveraineté plutôt qu'isolement réseau

Date : 2026-07-02 · Statut : accepté

## Contexte

Depuis l'origine, le projet se décrit comme « entièrement local, aucun cloud ».
La planification des capacités « Monde extérieur » (réponse sourcée, météo,
briefing RSS, lecture de page — CONTEXT.md § phase 6) rend cette formule
ambiguë : ces capacités exigent des requêtes Internet sortantes, alors que la
lettre de la contrainte les interdit. Il fallait trancher ce que « local »
protège vraiment.

## Décision

La contrainte fondatrice est reformulée en **souveraineté** :

- Les **modèles** (LLM, STT, TTS, embeddings) s'exécutent en local — aucun
  service d'IA cloud, jamais.
- Les **données personnelles** (mémoire, conversations, agenda, documents)
  restent en local et ne sont jamais transmises à un tiers.
- Les **requêtes sortantes anonymes** sont permises : recherche web (via un
  méta-moteur auto-hébergé type SearXNG), API météo sans clé ni compte,
  flux RSS publics.

Le glossaire (CONTEXT.md, terme « Souveraineté ») fait foi.

## Justification

- Un assistant vocal qui ignore la météo, l'actualité et le web répond mal à
  son usage quotidien ; l'isolement strict sacrifiait l'utilité à une pureté
  que personne n'exigeait.
- Ce que l'utilisateur protège, ce sont ses données et son indépendance des
  IA cloud — pas l'absence de trafic réseau. Une requête météo anonyme ne
  compromet ni l'un ni l'autre.
- La frontière reste vérifiable : aucune donnée issue de la mémoire, des
  conversations ou de l'agenda ne figure dans une requête sortante ; seuls
  les termes de recherche formulés pour la question courante sortent.

## Alternatives écartées

- **Isolement strict (zéro requête sortante)** : condamnait toute la phase
  Monde extérieur ; utilité trop réduite pour un assistant du quotidien.
- **Cas par cas avec interrupteur hors-ligne global** : complexité de
  configuration et de test pour un besoin non exprimé ; pourra être ajouté
  plus tard sans casser la présente décision.
- **Services cloud avec compte (agenda Google, API météo à clé)** : réintroduit
  la dépendance et l'exposition des données personnelles que le projet refuse
  (l'agenda retenu est local et neuf).
