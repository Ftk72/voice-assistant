// Empêche l'ouverture d'une console Windows superflue en mode release.
// Réf. https://v2.tauri.app/start/create-project/
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

// Toute la logique vit dans la bibliothèque `coquille_lib` (cf. lib.rs) ;
// ce point d'entrée ne fait que la lancer.
fn main() {
    coquille_lib::run()
}
