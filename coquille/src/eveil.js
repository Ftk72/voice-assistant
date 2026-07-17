// Mot d'éveil — détection continue dans la webview (ticket wayfinder 0010).
//
// ADR 0012 décision 2 : le mot d'éveil tourne DANS LE NAVIGATEUR — l'audio ne
// quitte pas la webview en veille (« rien ne quitte la machine » poussé au
// processus). Aucun serveur n'entend la pièce tant que la conversation n'est
// pas ouverte.
//
// ADR 0012 décision 1 : le mot d'éveil **ouvre** la conversation, il ne
// re-filtre PAS chaque tour. Une fois ouverte, la conversation vit sa vie
// (micro ouvert, multi-tours) — d'où l'arrêt du moteur pendant qu'elle dure.
//
// ADR 0009 : la coquille affiche et relaie, elle ne décide pas. Détecter un mot
// d'éveil n'est pas une décision métier : c'est un **événement d'entrée**, de la
// même classe qu'un clic sur le bouton — et il déclenche exactement le même
// point d'entrée (`ouvrir()`), sans chemin parallèle.
//
// Pourquoi ici et non dans la pastille (enquête du 2026-07-17, ticket 0010) :
// la console détient déjà le micro, le bouton et l'ouverture de conversation ;
// la pastille n'a ni micro ni connexion et exigerait un relais montant de plus.
// Les deux fenêtres survivent également (`lib.rs` masque, ne ferme jamais), donc
// aucune ne l'emportait sur la survie. La formule « webview de la pastille » du
// ticket date d'avant la séparation console/pastille : son intention, celle de
// l'ADR 0012, est « dans la webview, pas côté serveur ».

import * as ort from "./eveil/ort/ort.wasm.bundle.min.mjs";
import { WakeWordEngine } from "./eveil/moteur.js";

// Mot d'éveil actif. `hey_jarvis` est un **canari anglais**, pas la destination :
// aucun modèle FR n'existe (recherche 0009), il doit être entraîné sur mesure.
// Le canari prouve la chaîne (WASM/WebView2, micro en veille, détection →
// ouverture) sans attendre cet entraînement. Quand le modèle FR sera là, il se
// dépose dans `eveil/modeles/` et seules ces deux constantes changent.
// Voir `eveil/PROVENANCE.md`.
const MOT_DEVEIL = "hey_jarvis";
const FICHIER_MODELE = "hey_jarvis_v0.1.onnx";

// Seuil de détection (0-1). Plus haut = moins de faux positifs, plus de ratés.
// À régler au réel : télé allumée, distance de pièce (critère du ticket 0010).
const SEUIL = 0.5;

// Le runtime est vendoré : on lui interdit toute autre source (ADR 0007). Il
// charge sa glue (`ort-wasm-simd-threaded.mjs`) et son binaire (`.wasm`) depuis
// ce dossier. Chemin **absolu depuis la racine** (et non relatif) : ORT résout
// `wasmPaths` par rapport à l'URL du bundle — déjà `/eveil/ort/` —, si bien
// qu'un `./eveil/ort/` se redoublerait en `/eveil/ort/eveil/ort/` (erreur
// « Failed to fetch … » au run réel, 2026-07-17).
// Mono-thread explicite — sans isolation cross-origin (COOP/COEP), ORT y
// retomberait de toute façon ; le dire évite qu'il tente de créer des workers.
ort.env.wasm.wasmPaths = "/eveil/ort/";
ort.env.wasm.numThreads = 1;

const moteur = new WakeWordEngine({
  keywords: [MOT_DEVEIL],
  modelFiles: { [MOT_DEVEIL]: FICHIER_MODELE },
  baseAssetUrl: "./eveil/modeles",
  executionProviders: ["wasm"],
  detectionThreshold: SEUIL,
});

// `console.js` (script classique, chargé avant ce module) expose le point
// d'entrée et annonce les transitions de conversation. On ne touche à rien
// d'autre de son état.
const console_ = () => window.coquilleEveil;

function tracer(message) {
  console_()?.tracer("Éveil: " + message);
}

// Le micro de la veille et celui de la conversation ne cohabitent pas : le
// moteur ouvre son propre `getUserMedia` (16 kHz, AudioWorklet). On le rend
// pendant la conversation, on le reprend au raccrochage.
async function ecouter() {
  try {
    await moteur.start();
    tracer("à l'écoute du mot d'éveil (« " + MOT_DEVEIL + " »).");
  } catch (err) {
    tracer("micro indisponible pour la veille : " + err);
  }
}

async function suspendre() {
  await moteur.stop();
  tracer("veille suspendue (conversation en cours).");
}

moteur.on("detect", ({ keyword, score }) => {
  tracer("détecté « " + keyword + " » (score " + score.toFixed(2) + ").");
  // Le mot d'éveil ouvre la conversation — exactement ce que fait le bouton.
  // `ouvrir()` est sans effet si une conversation est déjà en cours.
  console_()?.ouvrir();
});

moteur.on("error", (err) => tracer("erreur du moteur : " + err));

// La conversation prend le micro : on suspend la veille. Elle le rend : on
// reprend. C'est `console.js` qui annonce ces transitions (il est seul à tenir
// la connexion), la veille ne fait qu'y réagir.
window.addEventListener("conversation-ouverte", () => void suspendre());
window.addEventListener("conversation-fermee", () => void ecouter());

// Chargement des modèles (~5 Mo depuis le disque, aucun réseau), puis écoute.
// Si le chargement échoue, la coquille reste parfaitement utilisable au bouton :
// le mot d'éveil est un confort, jamais le chemin nominal (plan B du ticket
// 0010 — « le bouton reste le chemin nominal »).
(async () => {
  try {
    await moteur.load();
    tracer("moteur chargé (WASM, mono-thread).");
  } catch (err) {
    tracer("moteur indisponible, le bouton reste le chemin nominal : " + err);
    return;
  }
  await ecouter();
})();
