---
label: wayfinder:task
statut: clos
assigne: agent principal (session 2026-07-17)
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

## Clôture (session 2026-07-17) — le pilier tenait déjà, validé à l'oreille

**Audit des prémisses : le gros du ticket était déjà acquis.** Contrairement à
la prémisse (« `_RealChatterboxEngine` jamais exécuté, rien ne prouve qu'il
tourne, 1er échec probable = sm_120 »), le conteneur voice-forge en service
portait **déjà** l'extra chatterbox avec le bon torch :

- Extra installé dans le `.venv` uv de l'image : `chatterbox` présent,
  **torch 2.8.0+cu128** (piège de mesure évité : `docker compose exec … python`
  vise le Python de base torch 2.6 ; c'est `uv run python` qui vise le `.venv`
  de l'app). **Aucun téléchargement de 2,5 Go, aucun build de 20 min.**
- **sm_120 déjà franchi** : `torch.cuda.get_device_capability()` → `(12, 0)`,
  CUDA dispo. L'override `torch>=2.8,<2.9` cu128 du `pyproject.toml` (impasse
  sm_120 du 2026-07-06, déjà périmée) survit à la refonte. Rien à capturer.
- `VOICE_FORGE_PROVIDER=chatterbox` déjà réglé (compose), poids du fine-tune
  français présents dans `models/chatterbox/` (mode `from_local`).

**Validé au réel le 2026-07-17.** Synthèse serveur (aperçu `/admin`) : HTTP 200,
WAV **PCM16 mono 24 kHz, 2,12 s, non silencieux** (amplitude saturée = vraie
parole), **1,75 s en régime** — cohérent avec la référence 1,94 s (2026-07-06).
Le format PCM_S 16 bits confirme le fix anti-grésillement. **Écoute à l'oreille
au poste Windows** (`/admin`, bouton Aperçu) : **voix clonée française audible et
propre** (« tout marche »). Charger Chatterbox n'a **pas** paginé le LLM (mesuré
à chaud : 60 tokens en 1,87 s ≈ 32 tok/s, réf. 33 ; util GPU 7-16 % en
génération, pas la signature ~3 % de pagination). Docstring
`_RealChatterboxEngine` corrigé (« Jamais exécuté à ce jour » → daté du run réel).

Débloque **0015** (bascule des consommateurs vers la vraie voix).

## Critère de clôture (atteint)

`VOICE_FORGE_PROVIDER=chatterbox`, un `speaker.wav` déposé, l'aperçu `/admin`
restitue **la voix clonée audible** au poste Windows. Toute impasse sm_120 /
mémoire capturée à chaud.
