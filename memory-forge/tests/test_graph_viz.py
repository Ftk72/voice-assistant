"""Phase 5 — visualisation : voisinage d'entité (port), endpoint /graph, page /viz."""

import time

from app.graph.fake import InMemoryGraph
from app.schemas import EpisodeIn


async def graphe_peuple() -> InMemoryGraph:
    graph = InMemoryGraph()
    await graph.add_episode(
        EpisodeIn(content="Léa fait du Judo.", source="conversation", name="conversation lundi")
    )
    await graph.add_episode(
        EpisodeIn(
            content="Le Judo a lieu mercredi à 17h.",
            source="document",
            name="judo-club.md § Horaires",
        )
    )
    await graph.add_episode(
        EpisodeIn(content="Max déteste les épinards.", source="conversation", name="conversation")
    )
    return graph


class TestNeighborhood:
    async def test_voisinage_direct_relie_les_entites_d_un_meme_fait(self):
        graph = await graphe_peuple()

        result = await graph.neighborhood("Léa", depth=1)

        assert result.center == "Léa"
        assert set(result.nodes) == {"Léa", "Judo"}
        assert len(result.edges) == 1
        edge = result.edges[0]
        assert {edge.source, edge.target} == {"Léa", "Judo"}
        assert edge.text == "Léa fait du Judo."
        assert edge.provenance.source == "conversation"

    async def test_profondeur_2_atteint_le_document_via_l_entite_partagee(self):
        graph = await graphe_peuple()

        result = await graph.neighborhood("Léa", depth=2)

        document_edges = [e for e in result.edges if e.provenance.source == "document"]
        assert len(document_edges) == 1
        assert "mercredi à 17h" in document_edges[0].text
        # Max n'est relié ni à Léa ni au Judo : hors du voisinage.
        assert "Max" not in result.nodes


class TestGraphEndpoint:
    def test_get_graph_renvoie_le_voisinage(self, client):
        client.post(
            "/episodes",
            json={"content": "Léa fait du Judo.", "source": "conversation", "name": "conv"},
        )
        deadline = time.monotonic() + 5
        payload = {"edges": []}
        while time.monotonic() < deadline and not payload["edges"]:
            payload = client.get("/graph", params={"entity": "Léa", "depth": 1}).json()
            time.sleep(0.02)

        assert payload["center"] == "Léa"
        assert set(payload["nodes"]) == {"Léa", "Judo"}
        assert payload["edges"][0]["provenance"]["source"] == "conversation"


class TestVizPage:
    def test_la_page_est_servie(self, client):
        response = client.get("/viz")

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")
        # Les commandes du scénario visualisation : recherche + filtres.
        html = response.text
        assert "Memory Forge" in html
        for marker in ["recherche", "provenance", "validité"]:
            assert marker in html.lower(), f"marqueur absent : {marker}"
