---
label: wayfinder:task
statut: clos
assigne: subagent-opus (délégation 2026-07-16) + finition agent principal
bloque-par: [0001-menage-du-depot]
---

# Docs racine v2

## Question

Réécrire les documents racine pour la stack ADR 0009 (AFK, délégable) —
bloqué par « Ménage du dépôt » (le README décrit le compose v2, pas l'ancien) :

- **`README.md`** : réécriture complète (il décrit encore « OpenWebUI comme
  unique interface ») — schéma de la nouvelle architecture (coquille Tauri +
  pastille, Pipecat natif Windows, forges Docker, Pont hôte), lancement.
- **`docs/ACCEPTANCE.md` v2 + `docs/plan-de-tests.md` v2** : critères rejoués
  sur la nouvelle stack (l'ancien plan est caduc côté interface — ADR 0009) ;
  intégrer conversation par mot d'éveil/pastille, interruption, capture à la
  clôture. Trancher au passage le sort des mesures de référence (cf. carte,
  « Pas encore spécifié »).
- **`docs/OPENWEBUI.md`** : supprimer (l'historique git l'archive) ;
  `ACCEPTANCE-CAPACITES.md` / `ACCEPTANCE-MEMOIRE.md` : réaligner ou fusionner.
- **`CLAUDE.md`** : rafraîchir « État particulier » (contrat ADR 0012 livré,
  fixes TTS/STT en code…) au réel du jour de la clôture du ticket.
- Critère de clôture : plus aucune mention d'OpenWebUI comme composant vivant
  hors ADR/impasses/handoffs ; un nouvel arrivant comprend la stack en lisant
  README + CONTEXT.md seuls.

## Résolution (2026-07-16)

Documentation racine réécrite pour la stack ADR 0009 (délégation subagent opus,
finition inline). Livré : `README.md` (réécriture complète, schéma
d'architecture), `docs/ACCEPTANCE.md` v2 (cycle ADR 0012, spec de la recette
0011), `docs/plan-de-tests.md` v2, `ACCEPTANCE-CAPACITES/MEMOIRE` réalignés,
`CLAUDE.md` « État particulier » rafraîchi, `docs/OPENWEBUI.md` supprimé, README
des forges nettoyés. Décision tranchée : mesures de l'ancienne stack conservées
en repères historiques, cibles v2 exprimées en relatif (voix→voix ≤ 2 s).
Critère de clôture atteint : `grep -i openwebui` hors adr/impasses/handoffs/
wayfinder ne renvoie que des mentions historiques (sortie/abandon).
