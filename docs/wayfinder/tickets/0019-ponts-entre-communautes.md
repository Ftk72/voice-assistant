---
label: wayfinder:prototype
statut: clos
assigne: claude (session 2026-07-18, prototype puis implémentation)
bloque-par: [0018-sujets-dominants-nommes]
carte: carte-graphe-memoire
---

# Ponts entre communautés

## Question

Mettre en scène les **entités-ponts** — celles qui relient des communautés
(centralité d'intermédiarité, déjà calculée) : « Léa relie Travail et
Musique ». À prototyper :

- distinction visuelle des ponts (taille, halo, forme ?) sans écraser la
  hiérarchie de centralité existante ;
- une lecture dédiée (liste des ponts dans le panneau latéral, clic → la
  caméra cadre le pont et ses deux rives) ;
- seuil : à partir de quand une entité « est » un pont.

## Prototype (2026-07-18)

**Prémisse fausse relevée** : la centralité d'intermédiarité n'était *pas*
« déjà calculée » — `analyse.py` ne connaît que le degré. Le prototype la
calcule côté client (Brandes en JS, instantané sur ~260 nœuds) ; la version
réelle ira dans `analyse.py` en TDD après le verdict.

Prototype jetable dans la page `/viz` de memory-forge
(<http://127.0.0.1:8200/viz>), 3 variantes + témoin commutées par `?variant=`
ou par la barre flottante en bas (flèches ← → au clavier aussi) :

- **témoin** — la vue actuelle, sans ponts (référence) ;
- **A « Sceau en scène »** — marquage 3D permanent : cage blanche en fil de
  fer autour de chaque pont, étiquette toujours visible ; panneau inchangé ;
- **B « Registre latéral »** — section « Ponts » dans le panneau : phrases
  « X relie Travail et Musique » triées par intermédiarité ; clic → la caméra
  cadre le pont et ses rives (barycentre + recul), halo sur le pont, le reste
  s'estompe ; aucun marquage permanent en scène ;
- **C « Squelette des ponts »** — la variante est un mode : ponts en losanges
  blancs grossis, arêtes inter-communautés épaisses et ambrées, tout le reste
  terni et rétréci.

**Seuil prototypé** : est un pont toute entité dont le voisinage couvre au
moins N communautés (la sienne comprise), N réglable au slider de la barre
(2–5, défaut 2) ; l'intermédiarité sert au *classement*, pas à la
qualification, pour que le seuil reste explicable à voix haute.

Tout se retire en supprimant le bloc `PROTOTYPE 0019` de
`memory-forge/app/viz/index.html` (JS + CSS marqués + l'appel
`majPontsPrototype()` dans `chargerGrapheComplet`).

**Verdict utilisateur : variante C, seuil réglable de 2 à 10.**

## Résolution

**Tranché et livré le 2026-07-18.** La variante C « Squelette des ponts » est
retenue et implémentée en dur dans la page `/viz`, le prototype est retiré.

- **Distinction visuelle** : le squelette est un *mode* (case « ponts » dans
  l'en-tête), pas un marquage permanent — activé, les ponts deviennent des
  losanges blancs grossis (octaèdre translucide par-dessus la sphère), les
  arêtes inter-communautés s'épaississent en ambre (`#f0a63a`), tout le reste
  (nœuds ternis vers le gris, arêtes quasi noires, particules coupées)
  s'efface. Désactivé, la scène est exactement celle d'avant le ticket — la
  hiérarchie de centralité existante n'est jamais écrasée.
- **Lecture dédiée** : la liste au panneau latéral (variante B) n'est **pas
  retenue** — la lecture, c'est le mode lui-même.
- **Seuil** : est un pont toute entité dont le voisinage couvre au moins N
  communautés (la sienne comprise), N au curseur de l'en-tête (**2 à 10**,
  défaut 2, compteur de ponts en direct). L'intermédiarité sert au classement
  d'une liste, pas à la qualification : sans liste, elle est inutile —
  **le Brandes du prototype n'est pas conservé** et `analyse.py` reste
  inchangé (aucun code Python touché, donc pas de nouveaux tests ; à
  ressusciter si le 0021 « Trous structurels » en a besoin).
- Garde-fou : une exploration ciblée écrase les communautés (`fusionner`
  remet 0) — le mode se suspend (`state.ponts` vidé) plutôt que d'afficher
  des ponts faux ; recharger le graphe complet le réarme.
