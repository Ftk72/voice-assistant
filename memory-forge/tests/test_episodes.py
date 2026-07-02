import time


def wait_for_facts(client, query: str, timeout: float = 2.0) -> list[dict]:
    """L'extraction est asynchrone (202 + file) : on attend que le fait apparaisse."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        facts = client.get("/search", params={"q": query}).json()["facts"]
        if facts:
            return facts
        time.sleep(0.02)
    return []


def test_health_repond_ok(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_un_episode_de_conversation_devient_un_fait_retrouvable(client):
    response = client.post(
        "/episodes",
        json={
            "content": "Ma fille Léa commence le judo mercredi.",
            "source": "conversation",
            "name": "appel du 2026-07-02",
        },
    )

    assert response.status_code == 202
    facts = wait_for_facts(client, "judo")
    assert facts, "le fait n'est jamais apparu dans la recherche"
    assert "judo" in facts[0]["text"].lower()


def test_la_recherche_sans_resultat_renvoie_une_liste_vide(client):
    assert client.get("/search", params={"q": "inconnu"}).json()["facts"] == []


def test_un_fait_porte_sa_provenance_et_sa_validite(client):
    client.post(
        "/episodes",
        json={
            "content": "Le club de judo ouvre à dix-huit heures.",
            "source": "document",
            "name": "judo-club.md",
        },
    )

    fact = wait_for_facts(client, "judo")[0]

    assert fact["provenance"] == {"source": "document", "name": "judo-club.md"}
    assert fact["valid_at"] is not None
    assert fact["invalid_at"] is None


def test_forget_supprime_reellement_les_faits_d_une_entite(client):
    client.post(
        "/episodes",
        json={
            "content": "Léa fait du judo. Paul fait du tennis.",
            "source": "conversation",
            "name": "appel",
        },
    )
    assert wait_for_facts(client, "tennis")

    response = client.request("DELETE", "/facts", params={"entity": "Léa"})

    assert response.status_code == 200
    assert response.json()["forgotten"] == 1
    assert client.get("/search", params={"q": "judo"}).json()["facts"] == []
    assert client.get("/search", params={"q": "tennis"}).json()["facts"] != []
