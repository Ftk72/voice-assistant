//! Coquille — processus natif de l'assistant vocal (ADR 0009 / ADR 0010).
//!
//! La coquille ne contient AUCUNE logique métier : elle assemble des fenêtres
//! (console + pastille), une icône de zone de notification et un raccourci
//! global. Le dialogue, la voix et le persona vivent dans les forges ; les
//! vues web ne font qu'afficher.
//!
//! Les deux fenêtres (`console`, `pastille`) sont déclarées dans
//! `tauri.conf.json` (clé `app.windows`) ; ce module se contente de les
//! piloter (afficher / masquer / focus).

use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager, WebviewWindow,
};

/// Étiquettes des fenêtres, alignées sur `tauri.conf.json`.
const FENETRE_CONSOLE: &str = "console";
const FENETRE_PASTILLE: &str = "pastille";

/// Affiche la fenêtre si elle est masquée, la masque sinon.
/// Réf. API fenêtre : https://docs.rs/tauri/2/tauri/webview/struct.WebviewWindow.html
fn basculer_visibilite(fenetre: &WebviewWindow) {
    match fenetre.is_visible() {
        Ok(true) => {
            let _ = fenetre.hide();
        }
        _ => {
            let _ = fenetre.show();
            let _ = fenetre.set_focus();
        }
    }
}

/// Point d'entrée applicatif appelé par `main.rs`.
pub fn run() {
    tauri::Builder::default()
        // Raccourci global (afficher la pastille).
        // Réf. https://v2.tauri.app/plugin/global-shortcut/
        .setup(|app| {
            #[cfg(desktop)]
            {
                use tauri_plugin_global_shortcut::{
                    Code, GlobalShortcutExt, Modifiers, Shortcut, ShortcutState,
                };

                // Ctrl+Alt+Espace : révèle / masque la pastille.
                let raccourci_pastille =
                    Shortcut::new(Some(Modifiers::CONTROL | Modifiers::ALT), Code::Space);

                app.handle().plugin(
                    tauri_plugin_global_shortcut::Builder::new()
                        .with_handler(move |app, raccourci, evenement| {
                            // On agit à l'appui uniquement (pas au relâchement).
                            if raccourci == &raccourci_pastille
                                && evenement.state() == ShortcutState::Pressed
                            {
                                if let Some(pastille) = app.get_webview_window(FENETRE_PASTILLE) {
                                    basculer_visibilite(&pastille);
                                }
                            }
                        })
                        .build(),
                )?;

                app.global_shortcut().register(raccourci_pastille)?;
            }

            // Icône de zone de notification (tray).
            // Réf. https://v2.tauri.app/learn/system-tray/
            let item_console =
                MenuItem::with_id(app, "console", "Afficher / masquer la console", true, None::<&str>)?;
            let item_pastille =
                MenuItem::with_id(app, "pastille", "Afficher / masquer la pastille", true, None::<&str>)?;
            let item_quitter = MenuItem::with_id(app, "quitter", "Quitter", true, None::<&str>)?;
            let menu = Menu::with_items(app, &[&item_console, &item_pastille, &item_quitter])?;

            let mut tray = TrayIconBuilder::new()
                .tooltip("Assistant vocal")
                .menu(&menu)
                .show_menu_on_left_click(false)
                .on_menu_event(|app, evenement| match evenement.id.as_ref() {
                    "console" => {
                        if let Some(f) = app.get_webview_window(FENETRE_CONSOLE) {
                            basculer_visibilite(&f);
                        }
                    }
                    "pastille" => {
                        if let Some(f) = app.get_webview_window(FENETRE_PASTILLE) {
                            basculer_visibilite(&f);
                        }
                    }
                    "quitter" => app.exit(0),
                    _ => {}
                })
                .on_tray_icon_event(|tray, evenement| {
                    // Clic gauche : bascule la console.
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = evenement
                    {
                        let app = tray.app_handle();
                        if let Some(f) = app.get_webview_window(FENETRE_CONSOLE) {
                            basculer_visibilite(&f);
                        }
                    }
                });

            // L'icône par défaut n'existe qu'une fois les icônes générées
            // (`cargo tauri icon`, cf. README). On la pose si elle est là,
            // sinon le tray reste sans image plutôt que de faire paniquer
            // l'application.
            if let Some(icone) = app.default_window_icon() {
                tray = tray.icon(icone.clone());
            }
            tray.build(app)?;

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("erreur au lancement de la coquille Tauri");
}
