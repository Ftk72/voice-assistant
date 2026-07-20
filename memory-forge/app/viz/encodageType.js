// Encodage visuel du type d'entité (ticket wayfinder 0026) : associe chaque
// type de l'ontologie (app/graph/ontologie.py) à une primitive géométrique 3D
// distincte, superposée à la sphère du nœud (déjà prise par communauté/
// centralité, cf. index.html) — module pur, zéro THREE, zéro DOM, testable en
// isolation (node:test), même patron que adressabilite.js.
//
// La sphère (nœud sans type) et l'octaèdre (losange du mode ponts, ticket
// 0019) sont volontairement absents de ce catalogue.

export const FORMES_PAR_TYPE = {
  // Personne reste la sphère par défaut du nœud (type le plus fréquent, celui
  // qu'on ne veut surtout pas surcharger) — aucune primitive dédiée à
  // superposer, cf. glypheDuNoeud() dans index.html.
  Personne: "sphere",
  Lieu: "cone",
  Organisation: "boite",
  Animal: "tetraedre",
  Bien: "dodecaedre",
  Aliment: "icosaedre",
  Projet: "capsule",
  Activite: "tore",
};

export function formeDuType(type) {
  return FORMES_PAR_TYPE[type] ?? null;
}
