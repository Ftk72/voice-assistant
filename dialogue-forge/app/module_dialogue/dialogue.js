// Module d'interface du dialogue (A4). Servi par le Dialogue Forge, chargé en
// iframe dans l'onglet console (ADR 0009). Deux sources, comme acté au ticket
// 0008 :
//   - le REST du DF (même origine) pour le contenu : personas, création de
//     conversation, dérogation de voix, rejeu de l'historique ;
//   - le canal RTVI, tenu par la console, relayé ici par `postMessage` : c'est
//     lui qui porte le fil vif (transcriptions utilisateur, phrases assistant
//     au moment où leur synthèse est jouée — ADR 0010 décision 5).
// Aucune décision métier ici : la page affiche, le DF décide.

const menuPersona = document.getElementById("menu-persona");
const menuVoix = document.getElementById("menu-voix");
const etat = document.getElementById("etat-conversation");
const fil = document.getElementById("fil");
const zoneOutils = document.getElementById("outils");
const listeOutils = document.getElementById("liste-outils");

let conversation = null; // id de la conversation courante
let liveAdopte = false; // a-t-on adopté l'id de la conversation *live* du transport ?
let bulleAssistant = null; // bulle en cours de remplissage au fil de la synthèse

// Remonte une commande à la console (fenêtre parente) qui l'émettra en RTVI
// client-message vers le transport. En usage isolé (pas d'iframe), `parent`
// vaut `window` : le message se poste à soi-même et personne ne l'écoute
// (la page ne traite que `source:"rtvi"`), donc sans effet — inoffensif.
function envoyerCommande(type, data) {
  window.parent?.postMessage({ source: "commande", type, data }, "*");
}

// --- REST du Dialogue Forge (même origine) ---------------------------------

async function chargerPersonas() {
  const personas = await (await fetch("/personas")).json();
  menuPersona.innerHTML = "";
  for (const p of personas) {
    const opt = document.createElement("option");
    opt.value = p.nom;
    opt.textContent = p.nom;
    opt.dataset.voix = p.voix;
    menuPersona.append(opt);
  }
  // Menu voix : les voix distinctes connues des personas (v1 — la liste
  // complète des voix enrôlées, servie par voice-forge, viendra plus tard :
  // elle demande un accès cross-forge à cadrer, cf. ticket 0008).
  const voix = [...new Set(personas.map((p) => p.voix))];
  menuVoix.innerHTML = "";
  for (const v of voix) {
    const opt = document.createElement("option");
    opt.value = v;
    opt.textContent = v;
    menuVoix.append(opt);
  }
}

async function nouvelleConversation(persona) {
  const reponse = await fetch("/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ persona }),
  });
  const { id } = await reponse.json();
  conversation = id;
  bulleAssistant = null;
  fil.innerHTML = "";
  listeOutils.innerHTML = "";
  zoneOutils.hidden = true;
  // La voix affichée suit le persona choisi (aucune dérogation au départ).
  const opt = menuPersona.selectedOptions[0];
  if (opt) menuVoix.value = opt.dataset.voix;
  await rejouerHistorique();
}

async function rejouerHistorique() {
  if (!conversation) return;
  const vue = await (await fetch(`/conversations/${conversation}`)).json();
  for (const message of vue.historique) {
    if (message.role === "user") ajouterTour("utilisateur", message.content);
    else if (message.role === "assistant" && message.content)
      ajouterTour("assistant", message.content);
  }
}

// Adopte l'id de la conversation *live* tenue par le transport (annoncée par
// server-message). Dès lors, les menus voix/historique visent cette conversation
// et non plus la fantôme créée en repli à l'amorçage (ticket 0008).
async function adopterConversationLive({ id, persona }) {
  liveAdopte = true;
  conversation = id;
  bulleAssistant = null;
  fil.innerHTML = "";
  listeOutils.innerHTML = "";
  zoneOutils.hidden = true;
  if (persona) {
    menuPersona.value = persona;
    const opt = menuPersona.selectedOptions[0];
    if (opt) menuVoix.value = opt.dataset.voix; // voix par défaut du persona live
  }
  await rejouerHistorique();
}

async function derogerVoix(voix) {
  if (!conversation) return;
  await fetch(`/conversations/${conversation}/voix`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ voix }),
  });
}

// --- Rendu du fil ----------------------------------------------------------

function ajouterTour(classe, texte) {
  const li = document.createElement("li");
  li.className = `tour ${classe}`;
  li.textContent = texte;
  fil.append(li);
  fil.parentElement.scrollTop = fil.parentElement.scrollHeight;
  return li;
}

function ajouterOutil(nom) {
  zoneOutils.hidden = false;
  const li = document.createElement("li");
  li.textContent = nom;
  listeOutils.append(li);
}

// --- Fil vif depuis le relais RTVI (postMessage de la console) -------------
// Le message relayé : `{source:"rtvi", type, data}` (cf. console.js). On ne
// retient que ce qui a un sens dans le fil ; le reste (métriques, niveaux
// audio…) est ignoré.

function traiterEvenementRtvi(type, donnees) {
  switch (type) {
    case "user-transcription":
      // STT batch = transcription finale ; on ignore les partielles.
      if (donnees?.final && donnees.text) ajouterTour("utilisateur", donnees.text);
      break;
    case "bot-started-speaking":
      etat.textContent = "parle";
      bulleAssistant = ajouterTour("assistant", "");
      break;
    case "bot-tts-text":
      // Phrase affichée au moment où sa synthèse est jouée (ADR 0010 déc. 5).
      if (donnees?.text) {
        if (!bulleAssistant) bulleAssistant = ajouterTour("assistant", "");
        bulleAssistant.textContent += (bulleAssistant.textContent ? " " : "") + donnees.text;
        fil.parentElement.scrollTop = fil.parentElement.scrollHeight;
      }
      break;
    case "bot-stopped-speaking":
      etat.textContent = "écoute";
      bulleAssistant = null;
      break;
    case "bot-interrupted":
      // Coupé : on fige la bulle en l'état (le non-prononcé n'a jamais été
      // ajouté, puisqu'il n'a pas produit de `bot-tts-text`).
      etat.textContent = "écoute";
      bulleAssistant = null;
      break;
    case "user-started-speaking":
    case "user-stopped-speaking":
      etat.textContent = "écoute";
      break;
    case "server-message":
      // Message serveur RTVI émis par le transport pour ce que les événements
      // RTVI natifs ne portent pas (le DF remplace l'étage LLM). Deux payloads :
      //   - {kind:"outil-appele", nom} : un outil vient d'être appelé ;
      //   - {kind:"conversation", id, persona} : l'id de la conversation *live*
      //     tenue par le transport. On l'adopte pour que les menus (voix,
      //     historique) visent la vraie conversation, pas la fantôme (0008).
      if (donnees?.kind === "outil-appele" && donnees.nom) ajouterOutil(donnees.nom);
      else if (donnees?.kind === "conversation" && donnees.id) adopterConversationLive(donnees);
      break;
    default:
      break;
  }
}

window.addEventListener("message", (e) => {
  if (e.data?.source === "rtvi") traiterEvenementRtvi(e.data.type, e.data.data);
});

// --- Câblage des menus + amorçage ------------------------------------------

// Changer de persona = nouvelle conversation (ADR 0012, persona pilote). En mode
// live, c'est le transport qui possède la conversation : on lui remonte la
// commande (il recréera et republiera l'id, qu'on adoptera). En repli isolé
// (pas encore de conversation live), on crée localement pour rester utilisable.
menuPersona.addEventListener("change", () => {
  envoyerCommande("persona", { nom: menuPersona.value });
  if (!liveAdopte) nouvelleConversation(menuPersona.value);
});
// La dérogation de voix vise la conversation courante (l'id live une fois
// adopté) — REST DF, même origine, effet au tour suivant (ADR 0012 déc. 5).
menuVoix.addEventListener("change", () => derogerVoix(menuVoix.value));

(async function amorcer() {
  await chargerPersonas();
  await nouvelleConversation(menuPersona.value || undefined);
})();
