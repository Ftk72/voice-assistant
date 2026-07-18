---
label: wayfinder:task
statut: clos
assigne: claude (session 2026-07-18, délégué haiku)
bloque-par: [0021-trous-structurels]
carte: carte-graphe-memoire
---

# Le graphe dans la coquille

## Question

Tranche fine finale : le graphe s'ouvre **depuis la console Tauri**, pattern
éprouvé du module dialogue A4 (iframe servie par la forge, entrée de
navigation dans la coquille, zéro logique métier côté coquille). À livrer :

- entrée de navigation (nav.js) vers `/viz` de memory-forge (port 8200) ;
- CORS/CSP côté memory-forge si la webview l'exige (piège connu du run réel :
  CORS coquille) ;
- validation au réel dans la coquille au poste Windows (HITL, relance du
  process natif après toute modif côté WSL).

## Résolution

**Livré le 2026-07-18** (délégué haiku, vérifié par l'agent principal :
relecture du diff des quatre fichiers, JSON de la CSP validé).

- **Navigation** : troisième onglet « Graphe » dans la coquille, section
  `#vue-graphe` + iframe vers `http://127.0.0.1:8200/viz`, pattern exact du
  module dialogue A4. Hauteur dédiée (`.graphe`, 70vh) : une scène 3D respire.
- **Chargement paresseux** : l'iframe porte un `data-src` que `nav.js` promeut
  en `src` à la première visite de l'onglet (mécanisme générique
  `iframe[data-src]`) — la scène WebGL ne se paie pas au démarrage de la
  console ; une fois chargée, l'iframe reste montée comme les autres.
- **CORS/CSP** : le piège pressenti n'était pas CORS (la page `/viz` est
  autonome, ses fetch sont same-origin) mais la **CSP Tauri** : `frame-src`
  étendu à `http://127.0.0.1:8200`. Aucun changement côté memory-forge (pas
  d'en-tête anti-iframe posé par la forge).
- Reste dû (HITL) : validation au réel au poste Windows — relancer
  `cargo tauri dev` (les modifs WSL n'entrent en vigueur qu'à la relance du
  process natif), onglet « Graphe », scène 3D vivante dans la coquille.
