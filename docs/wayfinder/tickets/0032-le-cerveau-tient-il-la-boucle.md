---
label: wayfinder:research
statut: clos
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

## Résolution (2026-07-20)

Note complète : [`docs/wayfinder/notes/verdict-boucle-codeact-qwen3.6.md`](../notes/verdict-boucle-codeact-qwen3.6.md).

- **Verdict : le modèle tient la boucle courte du palier 1**, testé sur 5
  tâches types (créer/relire, CSV→JSON, script+exécution, calcul multi-pas,
  lire→calculer→écrire), dans les **deux modes** (tool-calling natif
  llama.cpp et CodeAct) : 5/5 en natif (une erreur d'outil factice
  correctement contournée par le modèle, pas une hallucination), 5/5 en
  CodeAct. Aucune boucle infinie, aucune vraie dérive anglaise dans le canal
  destiné à la voix.
- **CodeAct converge en moins de pas** (souvent 1, contre 2-5 en natif) mais
  la mesure est optimiste : les outils simulés sont déterministes et sans
  latence, un Atelier réel forcerait plus d'allers-retours. Le mode natif
  garde l'avantage d'un journal d'Actions plus fin.
- **Plan B non engagé** (verdict positif) mais dimensionné pour mémoire :
  Qwen2.5-Coder-7B-Instruct, Hermes-3-Llama-3.1-8B ou xLAM-7b-fc-r en GGUF,
  tous tiendraient dans les 8,5 Go de VRAM libres mesurés à côté du 35B déjà
  chargé — aucun téléchargement engagé, aucun test réel fait.

Débloque le ticket 0033 (l'Atelier sandbox jetable) — le cerveau de la
boucle est qualifié.

## Critère de clôture

Un verdict mesuré (le modèle tient / ne tient pas la boucle courte, dans quel
mode d'action), et le plan B dimensionné si besoin — la boucle du palier 1
peut s'écrire sur du connu. **Atteint le 2026-07-20.**
