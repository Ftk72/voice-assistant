// Client voix de la console (ADR 0010 : audio par la webview ; ADR 0012 :
// bouton d'abord). Reprend la logique du prototype du transport voix
// (getUserMedia + RTCPeerConnection + POST /offer + lecture de la piste de
// retour), MAIS sans coturn ni `iceTransportPolicy: "relay"` : la coquille et
// le transport tournent sur le même hôte Windows, la media WebRTC passe donc
// en localhost (candidats « host »). Aucun serveur ICE n'est nécessaire.

// Le transport voix (Pipecat) écoute en natif Windows, co-localisé.
const URL_TRANSPORT = "http://127.0.0.1:8700";

const bouton = document.getElementById("bouton");
const etat = document.getElementById("etat");
const audio = document.getElementById("audio");
const journal = document.getElementById("journal");

let pc = null;

function tracer(msg) {
  journal.textContent += msg + "\n";
  journal.scrollTop = journal.scrollHeight;
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

  // Canal de données pour les événements RTVI (transcriptions, phrases).
  pc.createDataChannel("pipecat");

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
  bouton.textContent = "Parler";
  bouton.onclick = demarrer;
}

bouton.onclick = demarrer;
