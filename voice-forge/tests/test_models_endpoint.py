def test_v1_models_liste_le_modele_tts_au_format_openai(client):
    response = client.get("/v1/models")

    assert response.status_code == 200
    assert response.json() == {
        "object": "list",
        "data": [{"id": "tts-1", "object": "model", "owned_by": "voice-forge"}],
    }
