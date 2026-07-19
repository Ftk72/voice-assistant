---
label: wayfinder:prototype
statut: ouvert
assigne:
bloque-par: []
carte: carte-graphe-memoire
---

# Encodage visuel du type d'entité

## Question

Gradué de la brume le 2026-07-18 : les six types de l'ontologie (Personne,
Lieu, Organisation, Animal, Bien, Activité — `ontologie.py`) sont stockés en
label Neo4j mais jamais exposés par l'API (`NoeudGraphe`) ni rendus. Prototype
HITL (/prototype, l'utilisateur juge à l'œil dans `/viz`) :

- **Côté serveur (TDD)** : exposer le type dans `NoeudGraphe` — la petite
  tranche testable.
- **Côté rendu** : quel encodage pour quel type — forme du nœud, glyphe,
  trait ? — sans casser la palette Okabe-Ito des communautés (la couleur est
  prise) ni la lisibilité à l'échelle du graphe. Le corpus synthétique couvre
  les six types : jouable dès maintenant, au navigateur, sans la coquille.

**À-côté acté au grilling** : l'export d'une vue en image (bouton,
`canvas.toDataURL()`) se livre dans ce ticket — trivial, et c'est le véhicule
UI attendu.

## Critère de clôture

Un encodage validé à l'œil par l'utilisateur (ou renoncement argumenté),
livré dans `/viz` avec le type exposé par l'API sous test, et le bouton
d'export d'image présent.
