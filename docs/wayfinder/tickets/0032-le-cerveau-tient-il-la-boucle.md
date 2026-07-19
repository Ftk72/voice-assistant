---
label: wayfinder:research
statut: ouvert
assigne:
bloque-par: []
carte: carte-action-forge
---

# Le cerveau tient-il la boucle ? (Qwen3.6-35B-A3B en CodeAct)

## Question

La boucle observe-réfléchit-agit exige du LLM local qu'il enchaîne plusieurs
tours d'appels d'outils **en français** sans se perdre. Le modèle en place
(Qwen3.6-35B-A3B, MoE, servi par llama.cpp en OpenAI-compat sur 8001) est
réputé bon en appels d'outils — à **vérifier au réel**, pas à croire.

Research AFK, sur la stack existante (aucun téléchargement) :

- Sonder le modèle en boucle multi-étapes : 3 à 5 tâches types du palier 1
  (créer/convertir un fichier, petit script Python, calcul en plusieurs pas),
  prompt système en français, outils simulés — mesurer taux de réussite,
  nombre de pas, dérives (hallucination d'outil, boucle infinie, anglais).
- Comparer les modes d'action : appels d'outils natifs (tool calling
  llama.cpp) vs CodeAct pur (le modèle écrit du Python exécuté) — lequel ce
  modèle tient-il le mieux ?
- Verdict et plan B : si le modèle ne tient pas, dimensionner le plan B
  (modèle dédié agent à télécharger **par l'utilisateur** — candidats, VRAM
  face au 35B déjà chargé, bascule à la demande ?) sans l'engager.

Produit un compte rendu markdown lié en asset.

## Critère de clôture

Un verdict mesuré (le modèle tient / ne tient pas la boucle courte, dans quel
mode d'action), et le plan B dimensionné si besoin — la boucle du palier 1
peut s'écrire sur du connu.
