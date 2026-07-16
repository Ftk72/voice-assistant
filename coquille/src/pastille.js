// Pastille — présence permanente de l'assistant (CONTEXT.md). Elle n'affiche
// que l'état de conversation calculé par la console (seule à tenir la connexion
// WebRTC) et diffusé par l'événement Tauri `etat-pastille` : veille / écoute /
// parle. Aucune décision ici — la pastille écoute et affiche (ADR 0009).

const ETATS = {
  veille: { classe: "etat-veille", texte: "En veille" },
  ecoute: { classe: "etat-ecoute", texte: "À l'écoute" },
  parle: { classe: "etat-parle", texte: "L'assistant parle" },
};

const pastille = document.getElementById("pastille");
const texte = document.getElementById("pastille-texte");

function appliquer(nom) {
  const etat = ETATS[nom] ?? ETATS.veille;
  pastille.className = etat.classe;
  texte.textContent = etat.texte;
}

appliquer("veille");

// Écoute l'état diffusé par la console. `window.__TAURI__` est injecté par la
// coquille (`withGlobalTauri`) ; hors Tauri (page ouverte seule), la pastille
// reste en veille plutôt que d'échouer.
window.__TAURI__?.event.listen("etat-pastille", (evenement) => {
  appliquer(evenement.payload);
});
