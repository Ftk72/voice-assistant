# ADR 0003 — Administration des voix hors du frontend OpenWebUI (zéro fork)

Date : 2026-07-02 · Statut : **remplacé par l'ADR 0009** (2026-07-07 — sortie
complète d'OpenWebUI ; le principe « les mini-UI appartiennent aux forges »
survit et devient même la règle des modules d'interface)

## Contexte

La spec initiale demandait d'ajouter des pages au frontend OpenWebUI (Voice Manager, Voice Selector, micro, paramètres audio). Or trois de ces quatre éléments existent nativement : sélecteur de voix (peuplé via `GET {tts_base_url}/audio/voices`), paramètres audio (Settings → Audio), mode appel avec VAD et interruption (CallOverlay). Seule manque une UI d'import/clonage/aperçu/suppression des voix — tâche d'administration occasionnelle. L'intégrer au frontend Svelte imposerait un fork rebasé à chaque release (~2/mois).

## Décision

Aucune modification du frontend OpenWebUI. Le Voice Forge sert lui-même une **mini-page d'administration des voix** (style visuel calqué sur OpenWebUI), et détecte automatiquement les dossiers déposés dans `voices/`. L'usage quotidien (sélection de voix, conversation vocale) reste entièrement dans l'UI native d'OpenWebUI.

## Conséquences

- Zéro coût de rebase ; les mises à jour d'OpenWebUI restent triviales (pull d'image).
- L'utilisateur quitte OpenWebUI uniquement pour ajouter/cloner une voix (opération rare).
- La sélection par persona passe par `model.info.meta.tts.voice`, mécanisme natif.

## Alternatives écartées

- **Fork léger du frontend** : intégration parfaite mais dette de maintenance permanente ; contredit la règle « jamais de fork ».
- **Gestion par Tool conversationnel** : original mais peu pratique pour écouter des aperçus ; pourra s'ajouter plus tard sans rien casser.
