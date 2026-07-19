"""Contrefactuel « et si ? » (ticket wayfinder 0030) : masquer une entité ou un
fait et voir l'analyse (communautés, ponts, trous) se recalculer — le masque
est éphémère et purement visuel/analytique, jamais écrit en base."""

from app.schemas import GraphEdge, NoeudGraphe, Provenance
from app.viz.analyse import masquer

_PROVENANCE = Provenance(source="conversation", name="test")


def _arete(source: str, target: str, uuid: str | None = None) -> GraphEdge:
    return GraphEdge(
        source=source, target=target, text=f"{source}-{target}", provenance=_PROVENANCE, uuid=uuid
    )


class TestMasquer:
    def test_masquer_un_noeud_retire_ses_aretes_incidentes(self):
        noeuds = [NoeudGraphe(nom="Léa"), NoeudGraphe(nom="Judo")]
        aretes = [_arete("Léa", "Judo", "u1")]

        noeuds_restants, aretes_restantes = masquer(noeuds, aretes, ["Léa"], [])

        assert [n.nom for n in noeuds_restants] == ["Judo"]
        assert aretes_restantes == []

    def test_un_voisin_isole_par_le_masque_reste_present(self):
        noeuds = [NoeudGraphe(nom="Léa"), NoeudGraphe(nom="Judo")]
        aretes = [_arete("Léa", "Judo", "u1")]

        noeuds_restants, _ = masquer(noeuds, aretes, ["Léa"], [])

        noms = [n.nom for n in noeuds_restants]
        assert "Judo" in noms
        assert "Léa" not in noms

    def test_masquer_un_fait_par_uuid_ne_retire_que_lui(self):
        noeuds = [NoeudGraphe(nom="Léa"), NoeudGraphe(nom="Judo"), NoeudGraphe(nom="Karaté")]
        aretes = [_arete("Léa", "Judo", "u1"), _arete("Léa", "Karaté", "u2")]

        noeuds_restants, aretes_restantes = masquer(noeuds, aretes, [], ["u1"])

        assert [n.nom for n in noeuds_restants] == ["Léa", "Judo", "Karaté"]
        assert [a.uuid for a in aretes_restantes] == ["u2"]

    def test_masques_inconnus_ignores_sans_erreur(self):
        noeuds = [NoeudGraphe(nom="Léa"), NoeudGraphe(nom="Judo")]
        aretes = [_arete("Léa", "Judo", "u1")]

        noeuds_restants, aretes_restantes = masquer(
            noeuds, aretes, ["Fantôme"], ["uuid-inconnu"]
        )

        assert [n.nom for n in noeuds_restants] == ["Léa", "Judo"]
        assert [a.uuid for a in aretes_restantes] == ["u1"]


# --- Route HTTP `POST /et-si` (ticket wayfinder 0030) ---


def _attendre_graphe(client, timeout: float = 5.0):
    import time

    deadline = time.monotonic() + timeout
    payload = {"noeuds": []}
    while time.monotonic() < deadline and not payload["noeuds"]:
        payload = client.get("/graph/complet").json()
        time.sleep(0.02)
    return payload


class TestRouteEtSi:
    def _peupler_pont(self, client):
        # Léa relie deux amas (Judo/Karaté d'un côté, Piano/Peinture de l'autre)
        # via un fait qui joue le rôle de pont entre communautés.
        for phrase in [
            "Léa fait du Judo.",
            "Léa fait du Karaté.",
            "Léa fait du Piano.",
            "Léa fait de la Peinture.",
        ]:
            client.post(
                "/episodes", json={"content": phrase, "source": "conversation", "name": "conv"}
            )
        return _attendre_graphe(client)

    def test_masquer_un_pont_fait_differer_le_condense(self, client):
        graphe = self._peupler_pont(client)
        uuid_lea = next(n["uuid"] for n in graphe["noeuds"] if n["nom"] == "Léa")

        reponse = client.post("/et-si", json={"noeuds_masques": ["Léa"], "faits_masques": []})

        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["condense_reel"] != corps["condense_masque"]
        assert corps["condense_masque"]["nb_entites"] == corps["condense_reel"]["nb_entites"] - 1
        assert "Léa" not in {n["nom"] for n in corps["graphe"]["noeuds"]}
        assert uuid_lea  # sanity : l'uuid existait bien avant le masque

    def test_panier_vide_condense_reel_egal_condense_masque(self, client):
        self._peupler_pont(client)

        reponse = client.post("/et-si", json={})

        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["condense_reel"] == corps["condense_masque"]

    def test_aucune_ecriture_le_graphe_reel_reste_intact(self, client):
        graphe = self._peupler_pont(client)
        noms_avant = {n["nom"] for n in graphe["noeuds"]}

        client.post("/et-si", json={"noeuds_masques": ["Léa"], "faits_masques": []})

        graphe_apres = client.get("/graph/complet").json()
        noms_apres = {n["nom"] for n in graphe_apres["noeuds"]}
        assert noms_apres == noms_avant
        assert "Léa" in noms_apres
