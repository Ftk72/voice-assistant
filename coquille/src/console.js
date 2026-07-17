// Client voix de la console (ADR 0010 : audio par la webview ; ADR 0012 :
// bouton d'abord). Reprend la logique du prototype du transport voix
// (getUserMedia + RTCPeerConnection + POST /offer + lecture de la piste de
// retour), MAIS sans coturn ni `iceTransportPolicy: "relay"` : la coquille et
// le transport tournent sur le même hôte Windows, la media WebRTC passe donc
// en localhost (candidats « host »). Aucun serveur ICE n'est nécessaire.

// Le transport voix (Pipecat) écoute en natif Windows, co-localisé.
const URL_TRANSPORT = "http://127.0.0.1:8700";
// Le Dialogue Forge sert le module d'interface (iframe ci-dessous) ; on lui
// relaie le fil RTVI par postMessage, ciblé sur son origine.
const URL_DIALOGUE = "http://127.0.0.1:8600";

const bouton = document.getElementById("bouton");
const etat = document.getElementById("etat");
const audio = document.getElementById("audio");
const journal = document.getElementById("journal");

let pc = null;
let canal = null; // canal de données RTVI (ouvert dans demarrer)

function tracer(msg) {
  journal.textContent += msg + "\n";
  journal.scrollTop = journal.scrollHeight;
}

// Relais d'état vers la pastille (fenêtre séparée, sans connexion propre).
// La console est la seule à tenir la connexion WebRTC : elle traduit les
// événements RTVI du transport en état visuel (veille / écoute / parle) et le
// diffuse par un événement Tauri. La pastille n'écoute et n'affiche — aucune
// décision côté coquille (ADR 0009).
function emettreEtatPastille(nom) {
  window.__TAURI__?.event.emit("etat-pastille", nom);
}

// Relaie un événement RTVI au module d'interface (page du Dialogue Forge, servie
// en iframe). La console est la seule à tenir le canal de données ; elle
// transmet le fil (transcriptions, phrases assistant, états) à la page qui,
// elle, l'affiche. Aucune décision côté coquille (ADR 0009) : simple relais.
function relayerAuDialogue(type, data) {
  const iframe = document.getElementById("dialogue");
  iframe?.contentWindow?.postMessage({ source: "rtvi", type, data }, URL_DIALOGUE);
}

// Sens montant : la page du module (iframe) remonte des **commandes** (ex.
// changer de persona) ; la console est la seule à tenir le canal de données,
// elle les émet donc en RTVI client-message vers le transport. Toujours pas de
// décision côté coquille (ADR 0009) : simple relais dans l'autre sens.
window.addEventListener("message", (e) => {
  const m = e.data;
  if (!m || m.source !== "commande") return;
  if (!canal || canal.readyState !== "open") {
    tracer("Commande ignorée (canal fermé) : " + m.type);
    return;
  }
  canal.send(
    JSON.stringify({
      label: "rtvi-ai",
      type: "client-message",
      id: crypto.randomUUID(),
      data: { t: m.type, d: m.data },
    }),
  );
});

// Traite un message RTVI (Pipecat 1.5). Le fil : messages JSON
// `{label:"rtvi-ai", type, id, data}` envoyés bruts par le transport
// (SmallWebRTC `send_app_message`) sur le canal de données. Deux usages :
//   - la **pastille** ne retient que les transitions veille/écoute/parle ;
//   - le **module d'interface** (page du Dialogue Forge en iframe) reçoit
//     l'événement complet relayé — c'est lui qui affiche transcriptions et
//     phrases assistant (au timing de synthèse). La coquille ne fait que
//     relayer (ADR 0009).
function traiterMessageRtvi(donnees) {
  let msg;
  try {
    msg = JSON.parse(donnees);
  } catch {
    return; // keepalive « ping » ou trame non-JSON : ignorée
  }
  if (!msg || msg.label !== "rtvi-ai") return; // signalling & autres : ignorés
  tracer("RTVI: " + msg.type); // trace la voix du transport (types réellement émis)
  relayerAuDialogue(msg.type, msg.data); // fil vif → module d'interface
  switch (msg.type) {
    case "bot-started-speaking":
      emettreEtatPastille("parle");
      break;
    case "bot-stopped-speaking":
    case "bot-interrupted":
    case "bot-ready":
    case "user-started-speaking":
    case "user-stopped-speaking":
      emettreEtatPastille("ecoute");
      break;
    default:
      break;
  }
}

async function demarrer() {
  bouton.disabled = true;
  etat.textContent = "Connexion…";

  // Config ICE par défaut : localhost = candidats « host », pas de relais.
  pc = new RTCPeerConnection();

  pc.ontrack = (e) => {
    audio.srcObject = e.streams[0];
    tracer("Piste audio reçue.");
  };
  pc.onconnectionstatechange = () => {
    etat.textContent = "État : " + pc.connectionState;
    tracer("connectionState = " + pc.connectionState);
  };

  // Canal de données pour les événements RTVI (le transport s'attache au canal
  // que le client ouvre ; le label importe peu côté serveur). On y lit les
  // transitions veille/écoute/parle pour piloter la pastille.
  canal = pc.createDataChannel("pipecat");
  canal.onmessage = (e) => traiterMessageRtvi(e.data);

  // Micro (getUserMedia — AEC/NS/AGC du moteur Chromium/WebView2, ADR 0010).
  // addTrack crée un transceiver **sendrecv** : il envoie le micro ET reçoit
  // l'audio de l'assistant sur la même piste. NE PAS ajouter de transceiver
  // « audio » supplémentaire, sinon Pipecat lit une piste vide et coupe la
  // réception après ~3 s (impasse consignée côté transport).
  let flux;
  try {
    flux = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (err) {
    etat.textContent = "Micro indisponible : " + err.name;
    tracer("getUserMedia a échoué : " + err);
    bouton.disabled = false;
    return;
  }
  flux.getTracks().forEach((t) => pc.addTrack(t, flux));

  const offre = await pc.createOffer();
  await pc.setLocalDescription(offre);

  let reponse;
  try {
    reponse = await fetch(URL_TRANSPORT + "/offer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ sdp: offre.sdp, type: offre.type }),
    });
  } catch (err) {
    etat.textContent = "Transport injoignable.";
    tracer("POST /offer a échoué : " + err);
    bouton.disabled = false;
    return;
  }

  if (!reponse.ok) {
    etat.textContent = "Échec /offer : " + reponse.status;
    tracer(await reponse.text());
    bouton.disabled = false;
    return;
  }

  const answer = await reponse.json();
  await pc.setRemoteDescription(answer);
  tracer("Réponse SDP appliquée (pc_id=" + answer.pc_id + ").");
  etat.textContent = "En conversation.";
  // Conversation ouverte : la pastille passe de veille à écoute. Les
  // événements RTVI suivants (bot parle / se tait) affineront l'état.
  emettreEtatPastille("ecoute");
  bouton.textContent = "Raccrocher";
  bouton.disabled = false;
  bouton.onclick = raccrocher;
}

function raccrocher() {
  if (pc) {
    pc.close();
    pc = null;
  }
  if (audio.srcObject) {
    audio.srcObject.getTracks().forEach((t) => t.stop());
    audio.srcObject = null;
  }
  etat.textContent = "En veille.";
  emettreEtatPastille("veille");
  bouton.textContent = "Parler";
  bouton.onclick = demarrer;
}

bouton.onclick = demarrer;
