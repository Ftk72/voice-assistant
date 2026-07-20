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
        for marker in ["recherche", "provenance", "obsolète"]:
            assert marker in html.lower(), f"marqueur absent : {marker}"

    def test_le_bundle_3d_force_graph_est_servi(self, client):
        response = client.get("/viz/vendor/3d-force-graph.min.js")

        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
        assert len(response.content) > 100_000  # un vrai bundle, pas une page d'erreur

    def test_un_fichier_hors_du_dossier_vendor_est_refuse(self, client):
        response = client.get("/viz/vendor/..%2F..%2Fapp%2Fconfig.py")

        assert response.status_code == 404

    def test_le_module_adressabilite_est_servi(self, client):
        response = client.get("/viz/adressabilite.js")

        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
        assert "serialiser" in response.text

    def test_le_module_encodage_type_est_servi(self, client):
        response = client.get("/viz/encodageType.js")

        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
        assert "formeDuType" in response.text

    def test_le_module_lecture_temporelle_est_servi(self, client):
        response = client.get("/viz/lectureTemporelle.js")

        assert response.status_code == 200
        assert "javascript" in response.headers["content-type"]
        assert "presentALaDate" in response.text


class TestGrapheComplet:
    async def test_port_trie_par_degre_decroissant_et_respecte_la_limite(self):
        graph = await graphe_peuple()
        # Un fait de plus pour donner à Judo un degré 2 (Léa-Judo, Judo-mercredi
        # n'apporte rien de plus ici) — on ajoute un second lien vers Léa.
        await graph.add_episode(
            EpisodeIn(content="Léa fait de la Piscine.", source="conversation", name="conv2")
        )

        graphe = await graph.graphe_complet(limite=2)

        noms = [n.nom for n in graphe.noeuds]
        assert len(noms) == 2
        assert "Léa" in noms  # Léa est reliée à Judo et Piscine : la plus connectée.
        assert graphe.tronque is True

    async def test_port_sans_troncature_sous_la_limite(self):
        graph = await graphe_peuple()

        graphe = await graph.graphe_complet(limite=500)

        assert graphe.tronque is False
        assert {"Léa", "Judo", "Max"} <= {n.nom for n in graphe.noeuds}

    def test_endpoint_renvoie_le_graphe_enrichi(self, client):
        client.post(
            "/episodes",
            json={"content": "Léa fait du Judo.", "source": "conversation", "name": "conv"},
        )
        deadline = time.monotonic() + 5
        payload = {"noeuds": []}
        while time.monotonic() < deadline and not payload["noeuds"]:
            payload = client.get("/graph/complet").json()
            time.sleep(0.02)

        noms = {n["nom"] for n in payload["noeuds"]}
        assert {"Léa", "Judo"} <= noms
        assert all("communaute" in n and "centralite" in n for n in payload["noeuds"])
        # Type d'entité (ticket wayfinder 0026) : la clé sort toujours, même à None
        # tant qu'aucune correction manuelle (ticket 0029) ne l'a posée — l'adaptateur
        # factice n'assigne pas de type à l'extraction, seul le graphiti réel le fait
        # via les labels Neo4j (cf. app/graph/ontologie.py).
        assert all("type" in n for n in payload["noeuds"])

    def test_endpoint_filtre_par_provenance(self, client):
        client.post(
            "/episodes",
            json={"content": "Léa fait du Judo.", "source": "conversation", "name": "conv"},
        )
        client.post(
            "/episodes",
            json={
                "content": "Le Judo a lieu mercredi.",
                "source": "document",
                "name": "club.md",
            },
        )
        deadline = time.monotonic() + 5
        payload = {"aretes": []}
        while time.monotonic() < deadline and not payload["aretes"]:
            payload = client.get("/graph/complet", params={"provenance": "document"}).json()
            time.sleep(0.02)

        assert payload["aretes"]
        assert all(a["provenance"]["source"] == "document" for a in payload["aretes"])
