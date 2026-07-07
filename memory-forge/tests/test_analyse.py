"""Analyse en Python pur du graphe complet : communautés (propagation d'étiquettes)
et centralité par degré — roadmap B1 (vue 3D type InfraNodus)."""

from app.schemas import GraphEdge, Provenance
from app.viz.analyse import centralite_degre, detecter_communautes, enrichir

_PROVENANCE = Provenance(source="conversation", name="test")


def _arete(source: str, target: str) -> GraphEdge:
    return GraphEdge(
        source=source, target=target, text=f"{source}-{target}", provenance=_PROVENANCE
    )


class TestDetecterCommunautes:
    def test_deux_amas_disjoints_recoivent_des_communautes_distinctes(self):
        noeuds = ["Léa", "Judo", "Karaté", "Max", "Épinards"]
        aretes = [("Léa", "Judo"), ("Léa", "Karaté"), ("Max", "Épinards")]

        communautes = detecter_communautes(noeuds, aretes)

        assert communautes["Léa"] == communautes["Judo"] == communautes["Karaté"]
        assert communautes["Max"] == communautes["Épinards"]
        assert communautes["Léa"] != communautes["Max"]

    def test_noeud_isole_forme_sa_propre_communaute(self):
        noeuds = ["Léa", "Judo", "Solo"]
        aretes = [("Léa", "Judo")]

        communautes = detecter_communautes(noeuds, aretes)

        assert communautes["Solo"] not in {communautes["Léa"], communautes["Judo"]}

    def test_deterministe_sur_plusieurs_appels(self):
        noeuds = ["A", "B", "C", "D", "E", "F"]
        aretes = [("A", "B"), ("B", "C"), ("D", "E"), ("E", "F")]

        premier = detecter_communautes(noeuds, aretes)
        second = detecter_communautes(noeuds, aretes)

        assert premier == second


class TestCentraliteDegre:
    def test_le_noeud_le_plus_connecte_vaut_un(self):
        noeuds = ["Léa", "Judo", "Karaté", "Piscine"]
        aretes = [("Léa", "Judo"), ("Léa", "Karaté"), ("Léa", "Piscine")]

        centralites = centralite_degre(noeuds, aretes)

        assert centralites["Léa"] == 1.0
        assert 0 < centralites["Judo"] < 1.0

    def test_noeud_isole_vaut_zero(self):
        noeuds = ["Léa", "Judo", "Solo"]
        aretes = [("Léa", "Judo")]

        centralites = centralite_degre(noeuds, aretes)

        assert centralites["Solo"] == 0.0

    def test_graphe_sans_arete_ne_leve_pas(self):
        centralites = centralite_degre(["Solo"], [])

        assert centralites == {"Solo": 0.0}


class TestEnrichir:
    def test_enrichit_chaque_noeud_de_communaute_et_centralite(self):
        noms = ["Léa", "Judo", "Max"]
        aretes = [_arete("Léa", "Judo")]

        noeuds = enrichir(noms, aretes)

        par_nom = {n.nom: n for n in noeuds}
        assert par_nom["Léa"].communaute == par_nom["Judo"].communaute
        assert par_nom["Léa"].centralite == 1.0
        assert par_nom["Max"].centralite == 0.0
