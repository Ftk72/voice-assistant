---
label: wayfinder:research
statut: clos
assigne: claude (session 2026-07-19, délégué opus)
bloque-par: []
carte: carte-cerp
---

# CERP — Observer le dépôt (le produit et ses décisions)

## Question

Phase Observe, moitié « produit » : lire **tout le dépôt** sans rien
modifier ni conclure — code des six forges, transport-voix, coquille, stt ;
docs (13 ADR, impasses, handoffs, cartes wayfinder, README, CONTEXT.md,
CLAUDE.md) ; tests ; compose et scripts ; **historique git complet** (les
messages de commit sont de la main de l'utilisateur).

Produire `docs/cerp/observations-depot.md` : uniquement des observations
objectives, **séparées des interprétations**, patterns récurrents ET absences
récurrentes (ce qui n'est jamais fait, jamais utilisé, jamais toléré).
Recenser aussi les décisions datées traçables (ADR, grillings, verdicts de
tickets) — elles serviront d'évidence au CIR.

AFK, délégable (`/delegate`) ; aucun téléchargement.

## Critère de clôture

Le rapport d'observation du dépôt existe, factuel et sourcé (chemins,
commits), sans une ligne de spéculation — prêt à nourrir la reconstruction
du CIR.

## Verdict (2026-07-19)

Livré : `docs/cerp/observations-depot.md` — observations O-x.y sourcées
(surface, architecture, nommage, rituels, matériel, **absences**, arbre non
commité), tableau des 13 ADR + grillings + verdicts de tickets, hypothèses
H-1→H-6 confinées en §9 (confiance + condition de falsification). Vérifié
par l'agent principal : périmètre au `git status`, relecture intégrale,
contre-vérification des chiffres (une erreur corrigée : « grilling » figure
dans 3 corps de commit sur 57, pas 0 — O-6.5/O-4.6 rectifiées). Limites
déclarées en annexe (vues vendorées non lues ; `world-forge/` et
`action-forge/` nommés mais absents de l'arbre, consigné en O-1.7/O-6.9).
