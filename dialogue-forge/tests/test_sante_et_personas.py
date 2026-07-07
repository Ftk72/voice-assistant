from app.personas import charger_personas


def test_le_health_repond_ok(client):
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json() == {"status": "ok"}


def test_un_persona_off_record_est_reconnu_a_son_titre(personas_dir):
    # ADR 0011 : jeton « off-record » optionnel après la voix, dans le titre.
    (personas_dir / "fantome.md").write_text(
        "# Fantome (voix : Emma, off-record)\n\n```\nDiscret.\n```\n", encoding="utf-8"
    )
    personas = charger_personas(personas_dir)
    assert personas["fantome"].off_record is True
    assert personas["fantome"].voix == "Emma"  # le jeton ne pollue pas la voix
    assert personas["assistant"].off_record is False


def test_les_personas_sont_charges_au_bon_format(client):
    reponse = client.get("/personas")
    assert reponse.status_code == 200
    par_nom = {p["nom"]: p["voix"] for p in reponse.json()}
    # Le README et le fichier mal formé sont ignorés ; il reste deux personas.
    assert par_nom == {"Assistant": "Emma", "Batman": "Batman"}
