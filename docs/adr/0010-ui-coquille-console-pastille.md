# ADR 0010 — UI de la coquille : console + pastille, audio par la webview, modules web

Date : 2026-07-07 · Statut : accepté · Précise l'ADR 0009 (architecture modulaire)

## Contexte

L'ADR 0009 a acté la coquille Tauri comme carte son et assembleur de modules
d'interface servis par les forges, sans en dessiner l'UI. Session de grilling
du 2026-07-07 : forme de la coquille, chemin de l'audio, place du Rust,
sémantique des sélecteurs voix/persona, synchronisation texte/voix,
technologie du graphe mémoire. Contraintes matérielles : 64 Go RAM, RTX 5080
(WebGL accéléré dans WebView2), tout local.

## Décisions

1. **Deux surfaces** : une **console** (fenêtre principale à onglets —
   Dialogue, Mémoire, Voix, Agenda — chaque onglet chargeant le module servi
   par son forge) et une **pastille** compacte toujours au-dessus (état
   veille/écoute/parle, déclenchement manuel, notifications d'annonces même
   console fermée). Multi-fenêtres Tauri ; la pastille vit avec le tray.
2. **Curseur Rust maintenu (ADR 0009)** : Rust pour le processus coquille
   (fenêtres, tray, raccourcis globaux, IPC) ; les modules restent des pages
   web légères servies par leur forge. Pas de Rust/WASM dans les vues.
3. **Audio de conversation par la webview** : getUserMedia + client Pipecat
   JS dans WebView2 (moteur Chromium) → WebRTC vers Pipecat. On hérite
   gratuitement de l'annulation d'écho, de la réduction de bruit et de l'AGC
   du stack Chrome — indispensables à l'interruption illimitée (choix acté
   ADR 0009). Aucune pile audio Rust (webrtc-rs + cpal) : réécrire l'AEC est
   le piège identifié.
4. **Sélecteurs du module dialogue** : le **persona pilote, la voix déroge**.
   Choisir un persona sélectionne sa voix par défaut et **changer de persona
   démarre une nouvelle conversation** (l'historique est lié au persona ;
   cohérent avec le cache de préfixe LLM et le futur persona off-record).
   Changer de voix est instantané, sans changer de conversation (dérogation
   valable pour la conversation en cours).
5. **La voix précède le texte** : l'encadré de dialogue affiche chaque phrase
   au moment où sa synthèse commence à être jouée, via les événements client
   de Pipecat (protocole RTVI), **phrase par phrase**. Les phrases jamais
   prononcées (interruption) ne s'affichent jamais. Le mot à mot est une
   évolution possible, dépendante d'un alignement TTS non garanti.
6. **Graphe mémoire en 3D** : module `/viz` de memory-forge refondu avec
   **3d-force-graph** (three.js/WebGL, vendoré en local — pas de CDN,
   souveraineté). Exploration type InfraNodus : force-directed 3D, voisinage
   au clic, coloration par communautés, filtres par provenance et par date.
7. **Deux fronts en parallèle** : chemin critique voix (Pipecat + mot d'éveil
   → coquille v1 → retrait OpenWebUI) mené en session, modules UI sans
   dépendance (graphe 3D en tête) délégués en parallèle — composants
   disjoints, aucun fichier partagé.

## Conséquences

- La coquille Tauri naît multi-fenêtres d'emblée (console + pastille) ; la
  pastille est le porteur des notifications d'annonces exigées par le
  glossaire (« doublée d'une notification visuelle »), console fermée comprise.
- Le module dialogue consomme deux sources : le Dialogue Forge (REST/NDJSON,
  historique) et les événements RTVI de Pipecat (synchronisation voix/texte).
- memory-forge doit exposer ce que la visualisation 3D exige (graphe complet
  paginé, communautés, dates) — extensions REST à concevoir côté forge,
  jamais côté coquille.
- `personas/` reste la source des personas ; la dérogation de voix est un
  état de conversation du Dialogue Forge, pas un réglage global.

## Alternatives écartées

- **Modules en Rust/WASM (Leptos/Yew)** : maximum de Rust mais écosystème
  moins mûr, build lourd par forge, WebGL en bindings de toute façon — coût
  réel pour un gain idéologique.
- **UI native Rust (egui/iced) sans webview** : recrée le monolithe frontal
  écarté par l'ADR 0009 et tue le graphe 3D à coût raisonnable.
- **Pile audio Rust native (webrtc-rs + cpal)** : réimplémenter AEC/NS/AGC,
  des semaines de risque pour un gain nul à l'usage.
- **Deux menus voix/persona indépendants** : contredit la définition du
  Persona (CONTEXT.md) et produit des états surprenants.
- **Changement de persona conservant l'historique** : re-prefill à chaque
  bascule, ambiguïté mémoire, off-record inextricable.
- **Texte affiché en fin de tour seulement** : rien à suivre pendant que
  l'assistant parle.
- **Cosmograph** (layout GPU 2D, surdimensionné), **Neo4j Browser/Bloom**
  (outil d'admin, pas un module), **rendu wgpu maison** (réinventer three.js).
- **Voix d'abord puis extras en séquence** : écarté au profit des deux fronts
  parallèles (le big bang assumé rend le silence tolérable, la délégation
  rend le parallélisme peu coûteux).
