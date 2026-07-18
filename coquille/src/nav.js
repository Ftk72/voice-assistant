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
};

for (const onglet of onglets) {
  onglet.addEventListener("click", () => {
    const cible = onglet.dataset.vue;
    for (const autre of onglets) autre.classList.toggle("actif", autre === onglet);
    for (const [nom, section] of Object.entries(vues)) section.hidden = nom !== cible;
  });
}
