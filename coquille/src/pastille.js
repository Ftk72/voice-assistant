// Pastille — STUB visuel (v1). Aucun branchement RTVI réel : le clic fait
// simplement défiler les trois états (veille → écoute → parle) pour donner à
// voir le rendu. Le vrai pilotage viendra d'un événement du transport voix
// dans un lot ultérieur.

const ETATS = [
  { classe: "etat-veille", texte: "En veille" },
  { classe: "etat-ecoute", texte: "À l'écoute" },
  { classe: "etat-parle", texte: "L'assistant parle" },
];

const pastille = document.getElementById("pastille");
const texte = document.getElementById("pastille-texte");
let index = 0;

function appliquer(i) {
  const etat = ETATS[i];
  pastille.className = etat.classe;
  texte.textContent = etat.texte;
}

pastille.addEventListener("click", () => {
  index = (index + 1) % ETATS.length;
  appliquer(index);
});

appliquer(index);
