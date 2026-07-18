---
label: wayfinder:prototype
statut: clos
assigne: agent principal (session 2026-07-17/18, implémentation déléguée sonnet)
bloque-par: [0013-liste-complete-des-voix-enrolees]
---

# Réglage grand public voix + persona dans la coquille

## Question

Choix utilisateur au re-wayfinding 2026-07-17 : **surface neuve, grand public**
(la console A4 reste l'outil technique de suivi ; on veut EN PLUS un vrai
réglage propre). L'utilisateur choisit **son persona** et **sa voix** parmi la
**liste complète des voix enrôlées**, hors du contexte debug de la console.

Contraintes :
- **ADR 0009** : la coquille n'héberge **aucune logique métier** — le réglage
  est une **page servie par une forge**, montée dans la coquille (pattern
  voice-forge `/admin`, DF `module_dialogue` en iframe).
- S'appuie sur le contrat cross-forge tranché en **0013** pour la liste
  complète des voix.
- Rapport persona↔voix déjà modélisé (un persona porte une voix par défaut ;
  choisir une voix = dérogation) — cf. `personas/`, endpoint de dérogation DF
  livré en 0008.

Étape 1 = **prototype** (skill `/prototype`) de l'UX pour réagir concrètement
(où vit le réglage dans la coquille, comment persona et voix s'articulent,
aperçu ?), avant de livrer.

## Périmètre

- Concevoir (prototype) puis **livrer** le réglage : page servie par une forge,
  montée dans la coquille, sélection persona + voix (liste complète), effet réel
  sur la conversation.
- **Hors périmètre** : la console A4 (inchangée) ; l'enrôlement/clonage
  (0005/0012).

## Avancement (session 2026-07-17) — design verrouillé (étape 1 prototype faite)

- **Modèle retenu : A — préférence PERMANENTE** (choix utilisateur). Le réglage
  fixe *mon persona / ma voix par défaut*, persistés, adoptés par toute nouvelle
  conversation (mot d'éveil compris) — pas un réglage jetable de la conversation
  en cours. Implique un **nouvel état côté DF** (persona + voix par défaut
  réglables à chaud et persistés, au-delà du `settings.persona_defaut` statique).
- **UX retenue : variante B — « Formulaire de réglages »** (prototype jetable
  `dialogue-forge/app/reglage/PROTOTYPE-reglage.html`, 3 variantes A/B/C via
  `?variant=`). Deux lignes : *Personnalité* (select) + *Voix* = **liste
  complète des voix enrôlées** en vedette (liste scrollable, ▶ aperçu sur
  chacune, badge « voix du persona » sur la voix par défaut). Utilitaire, met
  en avant le cœur du 0013. Prototype à **jeter** une fois la vraie page livrée.

### Plan de livraison (reste à faire)

1. **DF backend (TDD ports/adaptateurs)** :
   - Route `GET /voix` — contrat 0013 : proxie `voice-forge/audio/voices` →
     `{voix:[{id,nom}]}`, repli sur les voix des personas si voice-forge KO ;
     réglage `DIALOGUE_FORGE_VOICE_FORGE_URL` (défaut `http://voice-forge:8100`,
     à ajouter au compose).
   - État de préférence persisté : `GET /reglage` + `PUT /reglage` →
     `{persona, voix}` (fichier JSON dans un dossier data, survit au restart).
   - Câblage : `POST /conversations` sans persona explicite adopte le persona
     **enregistré** (pas seulement `settings.persona_defaut`) et applique la
     voix par défaut enregistrée comme dérogation initiale.
2. **Page réglage servie par le DF** (`/reglage`, pattern `module_dialogue`) :
   variante B, consomme `/personas` + `/voix` + `/reglage`, aperçu réel.
3. **Coquille** : monter la page en iframe (surface neuve ; natif Windows →
   relance de la coquille).
4. **HITL poste Windows** : choisir persona + voix, vérifier que l'assistant en
   tient compte à la conversation suivante.

## Clôture (session 2026-07-17/18) — validé au réel au poste Windows

**Livré** (implémentation déléguée à un subagent sonnet, vérifiée par l'agent
principal — 54 tests verts, ruff clean, compose valide) :

- **DF backend** : port/adaptateurs `app/voix/` (`CatalogueVoix`, factice +
  `CatalogueVoixREST` vers voice-forge, **validé en réel**) ; `GET /voix`
  (liste complète, repli sur les voix des personas si voice-forge KO) ;
  `POST /voix/{id}/apercu` (proxy de l'aperçu) ; préférence permanente
  persistée (`app/preferences.py`, `GET`/`PUT /reglage/preference`, JSON dans
  le volume `dialogue-forge-data:/data`) ; `POST /conversations` sans persona
  explicite adopte le persona **et** la voix enregistrés (voix posée en
  `voix_derogee` initiale).
- **Page `/reglage`** servie par le DF (variante B figée au prototype), montée
  dans la **coquille** via un second iframe + navigation Console/Réglages
  (`nav.js` externe — la CSP `script-src 'self'` interdit l'inline ; les deux
  iframes restent montées pour que le canal RTVI de la console survive).
- Compose : `DIALOGUE_FORGE_VOIX_BACKEND=rest`, `DIALOGUE_FORGE_VOICE_FORGE_URL`,
  `DIALOGUE_FORGE_REGLAGE_PATH`, volume `dialogue-forge-data`.

**Validé au réel le 2026-07-18 au poste Windows** : depuis l'onglet Réglages de
la coquille, préférence enregistrée (persona assistant + voix Jackie parmi la
liste complète), puis conversation vocale : l'assistant **répond en Jackie**
(vérifié dans le flux du tour : phrases portant `voix: "Jackie"`, synthèse
voice-forge 1,52 s de parole réelle). Lenteur du premier tour = chargement à
froid de Chatterbox (~41 s, documenté), pas un défaut.

**Constat annexe hors périmètre** (à qualifier en 0011) : sur « donne-moi
l'heure », le LLM a **halluciné l'heure** (« quatorze heures vingt-trois » à
00h25) au lieu d'appeler time-forge — la boucle d'outils MCP ne s'est pas
déclenchée sur ce tour. La voix Jackie est aussi ~-12 dB sous les autres
(échantillon d'enrôlement faible) — piste : normalisation à l'enrôlement.

## Critère de clôture (atteint)

Depuis la coquille, un utilisateur choisit persona et voix parmi toutes les voix
enrôlées, proprement (hors console de debug), et l'assistant en tient compte —
validé au poste Windows.
