---
label: wayfinder:grilling
statut: ouvert
assigne:
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

## Critère de clôture

Le contrat cross-forge « liste complète des voix enrôlées pour un sélecteur »
est tranché et documenté (qui l'expose, sous quelle route, comment il se
rafraîchit), prêt à être consommé par 0014.
