// Bascule d'affichage entre les surfaces de la coquille (Console / Réglages).
// Purement présentationnel (ADR 0009 — aucune logique métier ici) : les deux
// iframes restent montées en permanence, on ne fait que les montrer/masquer.
// Ainsi le canal RTVI tenu par la console survit au passage dans les réglages.
// Fichier externe car la CSP de la coquille interdit les scripts inline
// (script-src 'self', cf. src-tauri/tauri.conf.json).

const onglets = document.querySelectorAll("#nav-vues .onglet");
const vues = {
  console: document.getElementById("vue-console"),
  reglages: document.getElementById("vue-reglages"),
  graphe: document.getElementById("vue-graphe"),
};

for (const onglet of onglets) {
  onglet.addEventListener("click", () => {
    const cible = onglet.dataset.vue;
    const section = vues[cible];

    // Chargement paresseux des iframes 3D (scène WebGL) : la iframe cible
    // doit avoir un data-src, que l'on promeut à src une seule fois. Ainsi,
    // les iframes lourdes ne se chargent qu'à la première visite de l'onglet
    // (ticket 0022, pattern du module dialogue A4, ADR 0009).
    const iframeAvecDataSrc = section.querySelector("iframe[data-src]");
    if (iframeAvecDataSrc) {
      iframeAvecDataSrc.src = iframeAvecDataSrc.dataset.src;
      iframeAvecDataSrc.removeAttribute("data-src");
    }

    for (const autre of onglets) autre.classList.toggle("actif", autre === onglet);
    for (const [nom, sectionVue] of Object.entries(vues))
      sectionVue.hidden = nom !== cible;
  });
}
