---
label: wayfinder:task
statut: ouvert
assigne: claude (session 2026-07-18)
bloque-par: []
---

# Qualité du clone à l'oreille (niveau de Jackie, réglages par voix)

## Question

Gradué de la brume le 2026-07-18 : le clone est audible (0012) et Jackie est la
voix par défaut système (0015) — on peut maintenant **juger à l'oreille** et
décider ce qui manque. HITL (l'oreille de l'utilisateur est le juge).

1. **Le niveau de Jackie** : ~-12 dB sous les autres voix (amplitude max
   8319/32768 sur une synthèse, quand clonek sature à 32768 — anomalie n° 2 du
   handoff 0017). Piste principale : **normaliser le `speaker.wav` à
   l'enrôlement** (voice-forge) plutôt que corriger en aval. À trancher, puis
   livrer (la carte porte l'exécution).
2. **Le zero-shot une-prise suffit-il ?** Sinon : plusieurs échantillons par
   voix, et/ou réglages par voix `exaggeration`/`cfg_weight` (`config.json`).
3. **Ré-enrôler Jackie ?** Si la normalisation se fait à l'enrôlement, les voix
   déjà enrôlées n'en bénéficient pas — décider si on ré-enrôle ou si on
   normalise aussi l'existant.

## Périmètre

- voice-forge (enrôlement/synthèse) ; jugement à l'oreille au poste Windows.
- **Hors périmètre** : la recette elle-même (0011, qui peut se jouer en
  parallèle et versera ses observations ici) ; la limite de taille du dépôt
  (hors périmètre de la carte).

## Avancement (session 2026-07-18) — cause mesurée, normalisation livrée

**Prémisses vérifiées, cause à la source.** Le `speaker.wav` de Jackie était
faible (crête **-11,7 dBFS**, RMS -29,9) et Chatterbox recopie le niveau de la
référence (crête synthèse 8319 ≈ crête référence 8559) ; aucune normalisation
n'existait à l'enrôlement (`create_voice` écrivait les octets tels quels).
Trouvaille bonus : les WAV décodés par ffmpeg sur `pipe:1` portent des tailles
RIFF/data à `0xFFFFFFFF` (en-tête de streaming) — Jackie « durait » 89 478 s
pour tout lecteur qui croit l'en-tête.

**Livré (TDD, 51 tests verts, ruff propre)** :

- `app/voices/normalisation.py` — `normaliser_wav_pcm16` : **RMS cible
  -20 dBFS, plafond de crête -1 dBFS** (méthode validée par l'utilisateur),
  Python pur (stdlib `wave`, vaut aussi pour les builds sans ffmpeg),
  meilleur-effort (non-PCM16 → inchangé), réécrit un en-tête sain au passage.
- Branchée dans `VoiceManager.create_voice` — point de passage unique des deux
  voies d'enrôlement (capture micro et dépôt).
- `scripts/renormaliser_voix.py` — re-normalisation en place des voix
  existantes, originaux sauvegardés en `speaker.avant-0023.wav`.

**Exécuté et mesuré** : les 4 voix re-normalisées (toutes à RMS -20, clonek
bridé crête à -23,2 — écart entre voix réduit de 8 dB à 3 dB). Synthèses de
contrôle après re-normalisation : Jackie RMS **-17,8 dBFS** vs clonek
-21,7 — l'écart de -12 dB est résorbé.

**Piège frais capturé dans `docs/impasses.md`** : le rebuild de l'image a
tenté de re-télécharger ~2,5 Go (cache BuildKit de la couche `uv sync` évincé)
→ build tué, code déployé par `docker cp` + `restart`. **Le conteneur diverge
de l'image** : le vrai rebuild appartient à l'utilisateur (bonne connexion).

**Reste (HITL)** : écoute utilisateur (annonce enceintes + coquille), décision
« une prise suffit / plusieurs échantillons / `config.json` par voix », et le
rebuild durable de l'image.

## Cadrage fidélité (grilling du 2026-07-18)

Le besoin s'est précisé au grilling : au-delà du niveau (résorbé ci-dessus),
le clone pèche à l'oreille sur **le timbre** (on ne reconnaît pas assez la
personne) **et la prosodie/l'accent** (débit, intonation). Stratégie actée :
**escalade douce**, du levier le moins cher au plus lourd, chaque palier jugé
en **A/B oreille** (original vs clone) avant d'engager le suivant :

1. **Échantillon de référence soigné** : les recommandations Resemble
   ([Hugging Face](https://huggingface.co/ResembleAI/chatterbox),
   [guide multilingue](https://replicate.com/resemble-ai/chatterbox-multilingual/readme))
   — la propreté prime sur la durée, mais 2 min+ améliorent nettement ;
   **référence française pour synthèse française** (l'accent fuit sinon) ;
   style d'élocution proche de l'usage cible (conversationnel). Ré-enrôler
   avec un tel échantillon (la normalisation 0023 s'applique au passage).
2. **Réglages par voix** (`config.json`) : défauts `exaggeration=0.5` /
   `cfg_weight=0.5` ; baisser `cfg_weight` vers **0,3** si le locuteur de
   référence a un débit rapide (recommandation amont pour le français) ;
   ajuster un paramètre à la fois.
3. **Hors ticket** : la montée **Chatterbox V3** (similarité locuteur et
   hallucinations annoncées meilleures) est notée en brouillard de la carte —
   déclenchée seulement si 1+2 laissent le verdict d'oreille insuffisant.

## Critère de clôture

Jackie sonne au même niveau que les autres voix sur une annonce enceintes et
dans la coquille ; le clone est jugé fidèle en A/B (timbre reconnu, prosodie
naturelle) après échantillon soigné et réglages par voix — ou l'insuffisance
est constatée et fait graduer la montée Chatterbox V3 depuis le brouillard.
