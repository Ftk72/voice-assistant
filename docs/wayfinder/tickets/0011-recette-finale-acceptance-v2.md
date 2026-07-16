---
label: wayfinder:task
statut: ouvert
assigne:
bloque-par: [0002-docs-racine-v2, 0005-enrolement-de-la-vraie-voix, 0006-experience-demenagement, 0008-module-dialogue-a4, 0010-mot-d-eveil-dans-la-webview]
---

# Recette finale ACCEPTANCE v2

## Question

**HITL — le portail de la destination.** Rejouer intégralement ACCEPTANCE v2
(écrite au ticket « Docs racine v2 ») sur la stack complète, vraie voix,
mot d'éveil actif :

- Conversation ouverte au mot d'éveil et à la pastille ; multi-tours micro
  ouvert ; fin par silence (fenêtre d'écoute de suite) et par arrêt explicite.
- Interruption : l'assistant se tait, et au tour suivant ne référence jamais
  l'inaudible (troncature `/interrompre`).
- Capture mémoire à la clôture (épisode user-only), injection au tour
  suivant d'une conversation ultérieure, recall vocal, oubli vocal.
- Annonce spontanée (minuteur → enceintes via Pont hôte) doublée du chemin
  visuel disponible.
- Mesures consignées face aux références de l'ancienne stack (2,88 s
  voix→voix, STT 0,15-0,5 s, TTS ~2 s, LLM ~33 tok/s).

Résolution = procès-verbal de recette (critère par critère, mesures). Tout
échec ne se corrige pas dans ce ticket : il ouvre son propre ticket correctif
et la recette se rejoue. La carte se clôt quand ce ticket est clos.
