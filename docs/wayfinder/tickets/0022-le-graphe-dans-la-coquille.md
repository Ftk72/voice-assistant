---
label: wayfinder:task
statut: ouvert
assigne:
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
