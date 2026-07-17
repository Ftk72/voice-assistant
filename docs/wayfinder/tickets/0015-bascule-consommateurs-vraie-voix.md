---
label: wayfinder:task
statut: ouvert
assigne:
bloque-par: [0012-clonage-reel-de-la-voix, 0005-enrolement-de-la-vraie-voix]
---

# Basculer tous les consommateurs sur la vraie voix

## Question

Ex-étapes 2 et 3 de l'ancien 0005, isolées au re-wayfinding 2026-07-17 : une
fois la vraie voix **enrôlée** (0005) et le clonage **audible pour de vrai**
(0012), sortir toute **VoixDeTest** du chemin nominal.

1. **Basculer les consommateurs** : `TIME_FORGE_ANNOUNCE_VOICE`, la voix par
   défaut du transport (`tts_voix_defaut`), les personas concernés
   (`personas/*.md`, `meta.tts.voice`) — plus aucune VoixDeTest en chemin
   nominal.
2. **Vérifier à l'oreille** : une **annonce time-forge sur les enceintes**
   (chemin Pont hôte / aplay-WSLg, validé sur l'ancienne stack) restitue la
   vraie voix.

Bloqué tant que 0012 (le clone doit être audible pour de vrai) et 0005 (la vraie
voix doit être enrôlée) ne sont pas clos.

## Périmètre

- Réglages/env des consommateurs + personas ; vérification annonce enceintes.
- **Hors périmètre** : le réglage grand-public interactif (0014) — ici c'est la
  **valeur par défaut système** qui bascule.

## Critère de clôture

Une annonce time-forge sur les enceintes parle avec **la vraie voix**, et aucun
chemin nominal ne référence plus une VoixDeTest.
