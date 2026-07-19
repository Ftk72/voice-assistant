"""Corrections ciblées du graphe (ticket wayfinder 0029) : corriger le type
d'une entité, invalider un fait faux, renommer une entité mal orthographiée,
annuler une invalidation manuelle — jamais de suppression physique, jamais de
fusion de doublons, jamais de PATCH générique (décisions actées)."""

import time

import pytest

from app.graph.base import CibleIntrouvable, CorrectionRefusee
from app.graph.fake import InMemoryGraph
from app.schemas import EpisodeIn


async def _graphe_lea_judo() -> InMemoryGraph:
    graph = InMemoryGraph()
    await graph.add_episode(
        EpisodeIn(content="Léa fait du Judo.", source="conversation", name="conv")
    )
    return graph


def _uuid_noeud(graphe, nom):
    return next(n.uuid for n in graphe.noeuds if n.nom == nom)


class TestCorrigerTypeFactice:
    async def test_pose_le_type_et_trace_la_correction(self):
        graph = await _graphe_lea_judo()
        uuid_lea = _uuid_noeud(await graph.graphe_complet(), "Léa")

        await graph.corriger_type(uuid_lea, "Personne")

        noeud = next(n for n in (await graph.graphe_complet()).noeuds if n.nom == "Léa")
        assert noeud.type == "Personne"
        assert noeud.corrige_geste == "type"
        assert noeud.corrige_le is not None

    async def test_uuid_inconnu_leve_cible_introuvable(self):
        graph = await _graphe_lea_judo()

        with pytest.raises(CibleIntrouvable):
            await graph.corriger_type("uuid-inexistant", "Personne")


class TestInvaliderFaitFactice:
    async def test_invalid_at_prend_la_valeur_de_valid_at(self):
        graph = await _graphe_lea_judo()
        graphe = await graph.graphe_complet()
        arete = graphe.aretes[0]

        await graph.invalider_fait(arete.uuid)

        graphe = await graph.graphe_complet()
        arete = graphe.aretes[0]
        assert arete.invalid_at == arete.valid_at
        assert arete.invalid_at is not None
        assert arete.corrige_geste == "invalidation"
        assert arete.corrige_le is not None

    async def test_uuid_inconnu_leve_cible_introuvable(self):
        graph = await _graphe_lea_judo()

        with pytest.raises(CibleIntrouvable):
            await graph.invalider_fait("uuid-inexistant")


class TestRenommerEntiteFactice:
    async def test_le_nouveau_nom_apparait_mais_le_texte_du_fait_reste_intact(self):
        graph = await _graphe_lea_judo()
        uuid_lea = _uuid_noeud(await graph.graphe_complet(), "Léa")

        await graph.renommer_entite(uuid_lea, "Léa Fontaine")

        graphe = await graph.graphe_complet()
        noms = {n.nom for n in graphe.noeuds}
        assert "Léa Fontaine" in noms
        assert "Léa" not in noms
        noeud = next(n for n in graphe.noeuds if n.nom == "Léa Fontaine")
        assert noeud.nom_precedent == "Léa"
        assert noeud.corrige_geste == "renommage"
        # Les textes des faits ne bougent jamais (citations historiques).
        assert graphe.aretes[0].text == "Léa fait du Judo."
        # Mais l'arête affiche bien le nouveau nom côté source/target.
        assert "Léa Fontaine" in (graphe.aretes[0].source, graphe.aretes[0].target)

    async def test_uuid_inconnu_leve_cible_introuvable(self):
        graph = await _graphe_lea_judo()

        with pytest.raises(CibleIntrouvable):
            await graph.renommer_entite("uuid-inexistant", "Nouveau nom")


class TestAnnulerInvalidationFactice:
    async def test_annule_une_invalidation_manuelle(self):
        graph = await _graphe_lea_judo()
        arete = (await graph.graphe_complet()).aretes[0]
        await graph.invalider_fait(arete.uuid)

        await graph.annuler_invalidation(arete.uuid)

        arete = (await graph.graphe_complet()).aretes[0]
        assert arete.invalid_at is None
        assert arete.corrige_geste is None

    async def test_refuse_l_annulation_d_une_invalidation_non_manuelle(self):
        graph = await _graphe_lea_judo()
        arete = (await graph.graphe_complet()).aretes[0]
        # Invalidation « apprise » (pas via `invalider_fait`) : aucune trace
        # `corrige_geste="invalidation"` n'a été posée.
        fait = graph._trouver_fait(arete.uuid)
        fait.invalid_at = fait.valid_at

        with pytest.raises(CorrectionRefusee):
            await graph.annuler_invalidation(arete.uuid)

    async def test_uuid_inconnu_leve_cible_introuvable(self):
        graph = await _graphe_lea_judo()

        with pytest.raises(CibleIntrouvable):
            await graph.annuler_invalidation("uuid-inexistant")


# --- Routes HTTP (ticket wayfinder 0029) ---


def _attendre_graphe(client, timeout: float = 5.0):
    deadline = time.monotonic() + timeout
    payload = {"noeuds": []}
    while time.monotonic() < deadline and not payload["noeuds"]:
        payload = client.get("/graph/complet").json()
        time.sleep(0.02)
    return payload


class TestRoutesCorrections:
    def _peupler(self, client):
        client.post(
            "/episodes",
            json={"content": "Léa fait du Judo.", "source": "conversation", "name": "conv"},
        )
        return _attendre_graphe(client)

    def test_route_type_pose_le_type_visible_dans_graph_complet(self, client):
        graphe = self._peupler(client)
        uuid_lea = next(n["uuid"] for n in graphe["noeuds"] if n["nom"] == "Léa")

        reponse = client.post("/corrections/type", json={"uuid": uuid_lea, "type": "Personne"})

        assert reponse.status_code == 200
        assert reponse.json() == {"status": "ok"}
        graphe = client.get("/graph/complet").json()
        noeud = next(n for n in graphe["noeuds"] if n["nom"] == "Léa")
        assert noeud["type"] == "Personne"

    def test_route_type_hors_ontologie_renvoie_422(self, client):
        graphe = self._peupler(client)
        uuid_lea = next(n["uuid"] for n in graphe["noeuds"] if n["nom"] == "Léa")

        reponse = client.post(
            "/corrections/type", json={"uuid": uuid_lea, "type": "PasUnType"}
        )

        assert reponse.status_code == 422

    def test_route_type_uuid_inconnu_renvoie_404(self, client):
        self._peupler(client)

        reponse = client.post(
            "/corrections/type", json={"uuid": "uuid-inexistant", "type": "Personne"}
        )

        assert reponse.status_code == 404

    def test_route_invalidation_puis_annulation(self, client):
        graphe = self._peupler(client)
        uuid_fait = graphe["aretes"][0]["uuid"]

        reponse = client.post("/corrections/invalidation", json={"uuid": uuid_fait})
        assert reponse.status_code == 200
        graphe = client.get("/graph/complet").json()
        arete = graphe["aretes"][0]
        assert arete["invalid_at"] == arete["valid_at"]
        assert arete["corrige_geste"] == "invalidation"

        reponse = client.post("/corrections/annulation", json={"uuid": uuid_fait})
        assert reponse.status_code == 200
        graphe = client.get("/graph/complet").json()
        assert graphe["aretes"][0]["invalid_at"] is None

    def test_route_annulation_d_une_invalidation_non_manuelle_renvoie_409(self, client):
        graphe = self._peupler(client)
        uuid_fait = graphe["aretes"][0]["uuid"]
        fait = client.app.state.graph._trouver_fait(uuid_fait)
        fait.invalid_at = fait.valid_at

        reponse = client.post("/corrections/annulation", json={"uuid": uuid_fait})

        assert reponse.status_code == 409

    def test_route_annulation_uuid_inconnu_renvoie_404(self, client):
        self._peupler(client)

        reponse = client.post("/corrections/annulation", json={"uuid": "uuid-inexistant"})

        assert reponse.status_code == 404

    def test_route_renommage(self, client):
        graphe = self._peupler(client)
        uuid_lea = next(n["uuid"] for n in graphe["noeuds"] if n["nom"] == "Léa")

        reponse = client.post(
            "/corrections/renommage", json={"uuid": uuid_lea, "nom": "Léa Fontaine"}
        )

        assert reponse.status_code == 200
        graphe = client.get("/graph/complet").json()
        noms = {n["nom"] for n in graphe["noeuds"]}
        assert "Léa Fontaine" in noms
        noeud = next(n for n in graphe["noeuds"] if n["nom"] == "Léa Fontaine")
        assert noeud["nom_precedent"] == "Léa"

    def test_route_renommage_nom_vide_renvoie_422(self, client):
        graphe = self._peupler(client)
        uuid_lea = next(n["uuid"] for n in graphe["noeuds"] if n["nom"] == "Léa")

        reponse = client.post("/corrections/renommage", json={"uuid": uuid_lea, "nom": "   "})

        assert reponse.status_code == 422

    def test_route_renommage_uuid_inconnu_renvoie_404(self, client):
        self._peupler(client)

        reponse = client.post(
            "/corrections/renommage", json={"uuid": "uuid-inexistant", "nom": "Nouveau"}
        )

        assert reponse.status_code == 404
