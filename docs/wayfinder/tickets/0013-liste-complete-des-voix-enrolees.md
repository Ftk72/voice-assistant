---
label: wayfinder:grilling
statut: clos
assigne: agent principal (session 2026-07-17)
bloque-par: []
---

# Cadrer l'accès cross-forge à la liste complète des voix enrôlées

## Question

Le « **reste ouvert** » du ticket 0008 (module dialogue A4) : le menu voix ne
liste aujourd'hui que les voix **distinctes des personas** (v1). Le réglage
grand-public (0014) — comme le menu A4 — a besoin de la **liste complète des
voix enrôlées**.

Tension d'architecture à trancher (dans le respect ADR 0009 — la coquille
n'assemble, ne décide pas) : **qui expose la liste complète au réglage ?**

- La liste des voix vit dans **voice-forge** (`GET /audio/voices` →
  `{voices:[{id,name}]}`, scan à chaque requête).
- Les **personas** vivent dans le **Dialogue Forge** (`GET /personas` →
  `[{nom, voix}]`), et un persona porte une voix par défaut.
- Le réglage grand-public a besoin des **deux**.

Options à départager :
1. **DF proxie voice-forge** : le DF expose une route « voix disponibles » qui
   agrège `voice-forge/audio/voices` — une seule origine pour la page réglage.
2. **La page réglage lit les deux forges** directement (voice-forge + DF) — plus
   de couplage côté page, CORS/CSP à cadrer.
3. **Une page servie par voice-forge** (qui détient les voix) tire les personas
   du DF.

Décider aussi : le rafraîchissement (une voix enrôlée en 0005 doit apparaître
sans redémarrage — le scan voice-forge le permet déjà côté API).

## Périmètre

- **Décision** (grilling/domain-modeling) + le contrat d'accès retenu.
- **Débloque 0014** et enrichit rétroactivement le menu A4.

## Décision (session 2026-07-17) — option 1 : le Dialogue Forge proxie voice-forge

**Contrat tranché (choix utilisateur).** Parmi les trois options, retenue :
**le DF expose une route « voix disponibles » qui agrège
`voice-forge/audio/voices`** — une seule origine pour la page.

Raison : la page A4 (servie par le DF, `app/module_dialogue`) et le réglage
grand-public (0014) ne parlent **déjà qu'au DF en même origine** (`/personas`,
`/conversations`). Le DF est l'agrégateur naturel — il possède déjà personas +
voix et orchestre, et dispose déjà d'un `httpx.AsyncClient` (mémoire, LLM).
L'option 1 garde « une seule origine pour la page », évite tout CORS/CSP, et ne
déporte aucune logique vers la coquille (ADR 0009 respecté : la page est servie
par une forge, pas assemblée par la coquille).

### Contrat d'accès (prêt à consommer par 0014)

- **Qui l'expose** : le Dialogue Forge (pas la page, pas la coquille).
- **Route** : `GET /voix` (DF), qui proxie `voice-forge GET /audio/voices`
  (`{voices:[{id,name}]}`) et renvoie la **liste complète des voix enrôlées**
  au format DF : `{"voix": [{"id": …, "nom": …}]}` (traduction `name`→`nom`
  pour rester idiomatique au DF, cf. `/personas` → `{nom, voix}`).
- **URL amont** : réglée par `Settings` du DF (`env_prefix DIALOGUE_FORGE_`),
  soit **`DIALOGUE_FORGE_VOICE_FORGE_URL`**, défaut `http://voice-forge:8100`
  (à ajouter au service `dialogue` du compose — absent à ce jour ; time-forge
  a déjà le pendant `TIME_FORGE_VOICE_FORGE_URL`).
- **Rafraîchissement** : **live**, proxy **sans cache** — voice-forge scanne
  `voices/` à chaque requête, donc une voix enrôlée en 0005 (dépôt ou micro)
  apparaît **sans redémarrage** dès le prochain ouvrir-menu.
- **Comportement dégradé** : si voice-forge est injoignable, `GET /voix`
  retombe sur les **voix référencées par les personas** (déjà connues du DF via
  `/personas`) plutôt que de vider le menu ; l'échec amont est loggé. Le menu
  reste donc toujours utilisable.
- **Consommateurs** : le menu voix A4 (remplace le dédup actuel
  `[...new Set(personas.map(p => p.voix))]` de `dialogue.js`, v1) **et** le
  réglage grand-public (0014).

### Reste à implémenter (relève de 0014, ou d'un lot dédié)

La **décision** est close ici (critère atteint). L'implémentation — route DF
`GET /voix` en TDD ports/adaptateurs, ajout de `DIALOGUE_FORGE_VOICE_FORGE_URL`
au compose, câblage du menu A4 sur `/voix` — est le premier geste de 0014, qui
en est le consommateur direct.

## Critère de clôture (atteint)

Le contrat cross-forge « liste complète des voix enrôlées pour un sélecteur »
est tranché et documenté (qui l'expose, sous quelle route, comment il se
rafraîchit), prêt à être consommé par 0014.
