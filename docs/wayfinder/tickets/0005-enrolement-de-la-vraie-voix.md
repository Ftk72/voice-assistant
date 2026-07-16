---
label: wayfinder:task
statut: ouvert
assigne:
bloque-par: []
---

# Enrôlement de la vraie voix

## Question

**HITL** (micro + navigateur Windows requis) — sortir de VoixDeTest :

1. **Capturer la vraie voix** via le module `/admin` de voice-forge (lot B2a,
   codé et testé côté contrat 201/415/409/422, **jamais exécuté en
   navigateur**) : `getUserMedia` + encodage WAV JS pur. La stack Docker
   suffit (pas besoin de la coquille — un navigateur Windows atteint
   voice-forge via mirrored/localhost).
2. **Basculer les consommateurs** : `TIME_FORGE_ANNOUNCE_VOICE`, la voix par
   défaut du transport (`tts_voix_defaut`), les personas concernés — plus
   aucune VoixDeTest en chemin nominal.
3. **Vérifier à l'oreille** : aperçu `/admin`, une annonce time-forge sur les
   enceintes (chemin Pont hôte, validé sur l'ancienne stack).

Résolution = vraie voix enrôlée et audible partout ; anomalies de la capture
micro en navigateur (s'il y en a) capturées à chaud dans `docs/impasses.md`.
