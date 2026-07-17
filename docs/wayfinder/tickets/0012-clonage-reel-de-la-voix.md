---
label: wayfinder:task
statut: ouvert
assigne:
bloque-par: []
---

# Clonage réel de la voix (Chatterbox sur la RTX 5080)

## Question

**Le pilier « faire marcher pour de vrai »** (choix utilisateur au re-wayfinding
2026-07-17). Le clonage zero-shot existe **sur le papier** — `ChatterboxProvider`
clone depuis un simple `voices/NomVoix/speaker.wav` — mais l'adaptateur du vrai
modèle (`_RealChatterboxEngine`) **n'a jamais été exécuté**, et rien ne prouve
qu'il tourne sur cette machine.

Faire tourner le clonage **réellement** et l'entendre :

1. **Installer le vrai moteur** : `uv sync --extra chatterbox` (~2,5 Go, tire
   torch) — **l'utilisateur lance** le gros téléchargement (convention
   CLAUDE.md ; commandes fournies au format `/newbie`). Dépendances lourdes en
   extra séparé, déjà déclaré.
2. **Exécuter `_RealChatterboxEngine`** et valider la compat **Blackwell
   sm_120** : aucun binaire CUDA n'est présumé compatible sans test réel
   (torch < 2.8 mort sur sm_120) — le premier échec probable est là, à capturer
   dans `docs/impasses.md`.
3. **Entendre un clone audible** depuis un `speaker.wav` de référence (aperçu
   `/admin`), puis basculer `VOICE_FORGE_PROVIDER=chatterbox`.

Pièges connus (registre `docs/impasses.md`, 2026-07-17) : le build chatterbox
(~20 min) et sa pression mémoire ont déjà fait **paginer le LLM** (débit ÷30) —
**redémarrer le LLM en dernier** après toute manip GPU ; borner `-j` sur toute
compilation.

## Périmètre

- Installer + exécuter le vrai Chatterbox, valider sm_120, entendre un clone.
- Le décodage multi-format à l'entrée relève de 0005 ; la bascule des
  **consommateurs** (annonces, voix par défaut, personas) relève de 0015.

## Critère de clôture

`VOICE_FORGE_PROVIDER=chatterbox`, un `speaker.wav` déposé, l'aperçu `/admin`
restitue **la voix clonée audible** au poste Windows. Toute impasse sm_120 /
mémoire capturée à chaud.
