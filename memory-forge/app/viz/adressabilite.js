// Adressabilité de la vue (ticket wayfinder 0025) : grammaire du hash d'URL
// qui capture l'état affiché du graphe — module pur, zéro DOM, zéro réseau,
// zéro import, pour rester testable en isolation (node:test) et réutilisable
// tel quel par un futur pilotage LLM (SSE — différé, hors périmètre ici).
//
// Grammaire, dans cet ordre, champs omis à leur valeur par défaut :
//   focus=<nom>&surligner=<nom,nom>&prof=<n>&ponts=<seuil>&2d=1

const PROFONDEUR_DEFAUT = "2";

export function serialiser(etat) {
  const parts = [];
  if (etat.focus) {
    parts.push("focus=" + encodeURIComponent(etat.focus));
  }
  if (etat.surligner && etat.surligner.length > 0) {
    parts.push("surligner=" + etat.surligner.map(encodeURIComponent).join(","));
  }
  if (etat.prof !== undefined && etat.prof !== PROFONDEUR_DEFAUT) {
    parts.push("prof=" + encodeURIComponent(etat.prof));
  }
  if (etat.ponts !== null && etat.ponts !== undefined) {
    parts.push("ponts=" + etat.ponts);
  }
  if (etat.deuxD) {
    parts.push("2d=1");
  }
  return parts.join("&");
}

export function analyser(hash) {
  const brut = hash.startsWith("#") ? hash.slice(1) : hash;
  const cles = new Map();
  if (brut) {
    for (const paire of brut.split("&")) {
      const i = paire.indexOf("=");
      if (i === -1) continue;
      cles.set(paire.slice(0, i), paire.slice(i + 1));
    }
  }

  const focusBrut = cles.get("focus");
  const focus = focusBrut !== undefined ? decodeURIComponent(focusBrut) : null;

  const surlignerBrut = cles.get("surligner");
  const surligner = surlignerBrut
    ? surlignerBrut.split(",").map(decodeURIComponent).filter((v) => v !== "")
    : [];

  const profBrut = cles.get("prof");
  const prof = profBrut !== undefined ? decodeURIComponent(profBrut) : PROFONDEUR_DEFAUT;

  const pontsBrut = cles.get("ponts");
  const ponts = pontsBrut !== undefined ? Number(pontsBrut) : null;

  const deuxD = cles.get("2d") === "1";

  return { focus, surligner, prof, ponts, deuxD };
}
