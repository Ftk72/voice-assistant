// Réglage grand public (persona + voix par défaut, ticket wayfinder 0014,
// modèle A — préférence PERMANENTE). Servi par le Dialogue Forge, même
// origine : toutes les requêtes sont relatives. Aucune logique métier ici :
// la page affiche et enregistre, le DF décide (persiste, applique aux
// nouvelles conversations).

const selPersona = document.getElementById("sel-persona");
const listeVoix = document.getElementById("liste-voix");
const compteVoix = document.getElementById("compte-voix");
const boutonEnregistrer = document.getElementById("enregistrer");
const confirmation = document.getElementById("confirmation");

let personas = []; // [{nom, voix}]
let voix = []; // [{id, nom}]
let voixChoisie = null;

function personaDe(nom) {
  return personas.find((p) => p.nom.toLowerCase() === (nom || "").toLowerCase());
}

async function charger() {
  const [reponsePersonas, reponseVoix, reponsePreference] = await Promise.all([
    fetch("/personas"),
    fetch("/voix"),
    fetch("/reglage/preference"),
  ]);
  personas = await reponsePersonas.json();
  voix = (await reponseVoix.json()).voix;
  const preference = await reponsePreference.json();

  selPersona.innerHTML = "";
  for (const p of personas) {
    const opt = document.createElement("option");
    opt.value = p.nom;
    opt.textContent = p.nom;
    selPersona.append(opt);
  }
  const personaPrefere = personaDe(preference.persona);
  if (personaPrefere) selPersona.value = personaPrefere.nom;

  voixChoisie = preference.voix || personaDe(selPersona.value)?.voix || null;
  rendreVoix();
}

function rendreVoix() {
  compteVoix.textContent = `Toutes les voix enrôlées (${voix.length}). ▶ pour écouter.`;
  const persona = personaDe(selPersona.value);
  listeVoix.innerHTML = "";
  for (const v of voix) {
    const ligne = document.createElement("div");
    ligne.className = "voix-row" + (v.id === voixChoisie ? " sel" : "");
    const estDefautDuPersona = persona && v.nom === persona.voix;
    ligne.innerHTML = `
      <span class="radio"></span>
      <span class="nom">${v.nom} ${estDefautDuPersona ? `<span class="badge">voix de ${persona.nom}</span>` : ""}</span>
      <button class="play" type="button" title="Écouter">▶</button>`;
    ligne.querySelector(".play").addEventListener("click", (e) => {
      e.stopPropagation();
      ecouter(v.id);
    });
    ligne.addEventListener("click", () => {
      voixChoisie = v.id;
      rendreVoix();
    });
    listeVoix.append(ligne);
  }
}

async function ecouter(voixId) {
  const reponse = await fetch(`/voix/${encodeURIComponent(voixId)}/apercu`, { method: "POST" });
  if (!reponse.ok) return;
  const blob = await reponse.blob();
  new Audio(URL.createObjectURL(blob)).play();
}

selPersona.addEventListener("change", () => {
  const persona = personaDe(selPersona.value);
  if (persona) voixChoisie = persona.voix;
  rendreVoix();
});

boutonEnregistrer.addEventListener("click", async () => {
  confirmation.hidden = true;
  const reponse = await fetch("/reglage/preference", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ persona: selPersona.value, voix: voixChoisie }),
  });
  if (reponse.ok) confirmation.hidden = false;
});

charger();
