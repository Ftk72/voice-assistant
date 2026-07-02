from app.catalog import load_catalog

CATALOGUE = """
[actions.navigateur]
description = "Ouvrir le navigateur web"
windows = ["cmd", "/c", "start", "https://exemple.fr"]
linux = ["xdg-open", "https://exemple.fr"]

[actions.mac_seulement]
description = "Action sans variante Windows ni Linux"
"""


def test_parsing_du_toml(tmp_path):
    path = tmp_path / "catalog.toml"
    path.write_text(CATALOGUE, encoding="utf-8")

    catalog = load_catalog(path)

    assert set(catalog) == {"navigateur", "mac_seulement"}
    navigateur = catalog["navigateur"]
    assert navigateur.name == "navigateur"
    assert navigateur.command_for("linux") == ["xdg-open", "https://exemple.fr"]
    assert navigateur.command_for("win32") == ["cmd", "/c", "start", "https://exemple.fr"]


def test_action_sans_variante_plateforme(tmp_path):
    path = tmp_path / "catalog.toml"
    path.write_text(CATALOGUE, encoding="utf-8")

    action = load_catalog(path)["mac_seulement"]

    assert action.command_for("linux") is None
    assert action.command_for("win32") is None


def test_catalogue_absent_est_vide(tmp_path):
    assert load_catalog(tmp_path / "inexistant.toml") == {}
