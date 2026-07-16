"""La coquille (WebView2) appelle le transport en cross-origin.

Son front est servi sous `http://tauri.localhost` (Tauri v2 sur Windows) alors
que le transport écoute sur `http://127.0.0.1:8700` : le navigateur émet un
préflight `OPTIONS /offer` avant le `POST`. Sans CORS, FastAPI répond
405 Method Not Allowed et la console ne peut jamais ouvrir la conversation
(constaté au premier run réel du 2026-07-10).
"""


def test_le_preflight_de_la_coquille_est_accepte(client):
    reponse = client.options(
        "/offer",
        headers={
            "Origin": "http://tauri.localhost",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert reponse.status_code == 200
    assert reponse.headers["access-control-allow-origin"] == "http://tauri.localhost"


def test_une_origine_etrangere_n_est_pas_autorisee(client):
    reponse = client.options(
        "/offer",
        headers={
            "Origin": "http://exemple.invalide",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in reponse.headers


def test_les_variantes_locales_passent_par_le_filet_regex(client):
    for origine in ("http://localhost:1420", "http://127.0.0.1:8700"):
        reponse = client.options(
            "/offer",
            headers={
                "Origin": origine,
                "Access-Control-Request-Method": "POST",
            },
        )
        assert reponse.status_code == 200, origine
        assert reponse.headers["access-control-allow-origin"] == origine
