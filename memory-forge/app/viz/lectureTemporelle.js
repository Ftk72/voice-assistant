// Lecture temporelle (ticket wayfinder 0027) : curseur « à cette date » sur
// valid_at/invalid_at — module pur, zéro THREE, zéro DOM, testable en
// isolation (node:test), même patron que encodageType.js/adressabilite.js.
//
// Décision actée (pas de fenêtre à deux bornes) : un fait est présent à la
// date T si valid_at est nul ou ≤ T, ET si invalid_at est nul ou > T. Les
// faits hors période s'estompent, ils ne disparaissent jamais (le layout 3D
// ne doit pas bouger quand on déplace le curseur).

// Facteur d'estompage, jamais une opacité absolue : les deux surfaces qui
// l'appliquent n'ont pas la même ligne de base (1.0 pour `.fait` dans le
// panneau, 0.55 pour linkOpacity dans la scène 3D). Posée en absolu, la
// valeur 0.5 ne ferait rien en 3D — c'est le même idiome multiplicatif que
// le `base = l.obsolete ? 0.5 : 1` de linkWidth, un seul langage visuel pour
// « hors période », qu'elle soit temporelle ou d'obsolescence.
// Un fait absent le dit par sa TEINTE, jamais par sa transparence : l'estompage
// par alpha (première tentative de ce ticket) s'est révélé illisible au réel.
// Deux couleurs, parce qu'un fait pas-encore-né et un fait périmé sont des
// objets inverses — les peindre pareil perdrait ce que le curseur révèle.
//
// Valeurs validées (skill dataviz, `validate_palette.js`) contre le fond
// #0e1013 et les couleurs de provenance #6ea8fe/#74c69d : séparation en vision
// normale et en daltonisme au-dessus des seuils. Ne pas retoucher à l'œil.
//
// COULEUR_FUTUR est volontairement proche du fond et désaturée (elle « lit
// comme du gris », ce que le validateur signale à raison) : ce qui n'existe
// pas encore doit reculer. Son faible contraste est compensé, comme le skill
// l'exige, par le relief textuel — décomptes sous le curseur et pastilles
// nommées dans le panneau de faits.
export const COULEUR_FUTUR = "#3a4150";
export const COULEUR_REVOLU = "#b5533c";

// Décompte des trois états à une date — sert le relief textuel du curseur
// (« 199 présents · 344 à venir · 13 révolus ») et, accessoirement, de point
// d'audit : si la scène semble ne rien faire, ces nombres disent tout de suite
// si c'est le calcul ou le rendu qui a lâché.
export function decompteTemporel(aretes, date) {
  const d = { present: 0, futur: 0, revolu: 0 };
  for (const arete of aretes) d[etatTemporel(arete, date)] += 1;
  return d;
}

// Les dates arrivent du JSON en chaînes ISO (ou déjà en `Date` côté tests) ;
// `null`/`undefined` restent tels quels pour laisser les appelants gérer
// l'absence de date sans planter sur `new Date(null)` (qui vaudrait 1970).
function aDate(valeur) {
  if (valeur === null || valeur === undefined) return null;
  return valeur instanceof Date ? valeur : new Date(valeur);
}

// Bornes calculées sur toutes les dates non nulles (valid_at ET invalid_at)
// des arêtes fournies — `null` si le corpus ne porte aucune date (curseur à
// désactiver côté UI), les deux bornes égales si une seule date existe.
export function bornesTemporelles(aretes) {
  let min = null;
  let max = null;
  for (const arete of aretes) {
    for (const brut of [arete.valid_at, arete.invalid_at]) {
      const date = aDate(brut);
      if (!date) continue;
      if (min === null || date < min) min = date;
      if (max === null || date > max) max = date;
    }
  }
  if (min === null) return null;
  return { min, max };
}

// Présence à la date T (borne unique, décision actée du ticket 0027).
export function presentALaDate(arete, date) {
  const t = aDate(date);
  const valid = aDate(arete.valid_at);
  const invalid = aDate(arete.invalid_at);
  if (valid !== null && valid > t) return false;
  if (invalid !== null && invalid <= t) return false;
  return true;
}

// Nuance l'estompage : un fait hors période l'est soit parce qu'il n'est pas
// encore valide à T (« futur »), soit parce qu'il l'était déjà plus (« revolu »).
export function etatTemporel(arete, date) {
  const t = aDate(date);
  const valid = aDate(arete.valid_at);
  const invalid = aDate(arete.invalid_at);
  if (valid !== null && valid > t) return "futur";
  if (invalid !== null && invalid <= t) return "revolu";
  return "present";
}
