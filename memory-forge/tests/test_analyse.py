"""Analyse en Python pur du graphe complet : communautés (propagation d'étiquettes)
et centralité par degré — roadmap B1 (vue 3D type InfraNodus)."""

from app.schemas import GraphEdge, NoeudGraphe, Provenance
from app.viz.analyse import (
    centralite_degre,
    detecter_communautes,
    detecter_trous,
    enrichir,
    nommer_communautes,
)

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


class TestNommerCommunautes:
    def test_garde_les_trois_plus_centrales_dans_l_ordre(self):
        noeuds = [
            NoeudGraphe(nom="Léa Fontaine", communaute=0, centralite=0.9),
            NoeudGraphe(nom="Judo", communaute=0, centralite=0.7),
            NoeudGraphe(nom="Karaté", communaute=0, centralite=0.5),
            NoeudGraphe(nom="Piscine", communaute=0, centralite=0.1),
        ]

        noms = nommer_communautes(noeuds)

        assert noms[0] == "Léa Fontaine · Judo · Karaté"

    def test_communaute_a_un_seul_membre_pas_de_separateur(self):
        noeuds = [NoeudGraphe(nom="Solo", communaute=1, centralite=0.3)]

        noms = nommer_communautes(noeuds)

        assert noms[1] == "Solo"

    def test_egalite_de_centralite_departagee_alphabetiquement(self):
        noeuds = [
            NoeudGraphe(nom="Zoé", communaute=0, centralite=0.5),
            NoeudGraphe(nom="Anna", communaute=0, centralite=0.5),
        ]

        noms = nommer_communautes(noeuds)

        assert noms[0] == "Anna · Zoé"

    def test_plusieurs_communautes_distinctes_retournent_des_entrees_distinctes(self):
        noeuds = [
            NoeudGraphe(nom="Léa", communaute=0, centralite=1.0),
            NoeudGraphe(nom="Max", communaute=1, centralite=1.0),
        ]

        noms = nommer_communautes(noeuds)

        assert noms == {0: "Léa", 1: "Max"}


def _communaute(prefixe: str, communaute: int, effectif: int) -> list[NoeudGraphe]:
    return [
        NoeudGraphe(nom=f"{prefixe}{i}", communaute=communaute, centralite=0.1)
        for i in range(effectif)
    ]


class TestDetecterTrous:
    def test_deux_grosses_communautes_sans_arete_forment_un_trou(self):
        noeuds = _communaute("a", 0, 3) + _communaute("b", 1, 3)
        noms_communautes = {0: "Travail", 1: "Maison"}

        trous = detecter_trous(noeuds, [], noms_communautes)

        assert len(trous) == 1
        trou = trous[0]
        assert (trou.sujet_a, trou.sujet_b) == ("Maison", "Travail")
        assert (trou.communaute_a, trou.communaute_b) == (1, 0)
        assert trou.nb_aretes == 0

    def test_une_seule_arete_inter_communautes_reste_un_trou(self):
        noeuds = _communaute("a", 0, 3) + _communaute("b", 1, 3)
        aretes = [_arete("a0", "b0")]
        noms_communautes = {0: "Travail", 1: "Maison"}

        trous = detecter_trous(noeuds, aretes, noms_communautes)

        assert len(trous) == 1
        assert trous[0].nb_aretes == 1

    def test_paire_trop_connectee_n_est_pas_un_trou(self):
        noeuds = _communaute("a", 0, 3) + _communaute("b", 1, 3)
        aretes = [_arete("a0", "b0"), _arete("a1", "b1")]
        noms_communautes = {0: "Travail", 1: "Maison"}

        trous = detecter_trous(noeuds, aretes, noms_communautes)

        assert trous == []

    def test_communaute_trop_petite_est_ignoree(self):
        # b n'a que 2 membres : sous le plancher, ignorée même si 0 arête avec a et c.
        noeuds = _communaute("a", 0, 3) + _communaute("b", 1, 2) + _communaute("c", 2, 3)
        noms_communautes = {0: "Travail", 1: "Trop petite", 2: "Loisirs"}

        trous = detecter_trous(noeuds, [], noms_communautes)

        assert len(trous) == 1
        assert 1 not in (trous[0].communaute_a, trous[0].communaute_b)
        assert {trous[0].sujet_a, trous[0].sujet_b} == {"Travail", "Loisirs"}

    def test_coupe_a_trois_et_ordre_par_produit_des_tailles_puis_alphabetique(self):
        # A(5), B(4), C(3), D(3), aucune arête : produits AB=20, AC=15, AD=15,
        # BC=12, BD=12, CD=9. Seuls les 3 premiers doivent survivre : AB, puis
        # AC/AD à égalité de produit, départagés alphabétiquement (C < D).
        noeuds = (
            _communaute("a", 0, 5)
            + _communaute("b", 1, 4)
            + _communaute("c", 2, 3)
            + _communaute("d", 3, 3)
        )
        noms_communautes = {0: "A", 1: "B", 2: "C", 3: "D"}

        trous = detecter_trous(noeuds, [], noms_communautes)

        assert len(trous) == 3
        paires = [(t.sujet_a, t.sujet_b) for t in trous]
        assert paires == [("A", "B"), ("A", "C"), ("A", "D")]

    def test_graphe_vide_renvoie_une_liste_vide(self):
        assert detecter_trous([], [], {}) == []


class TestCondenserRemplitLesTrous:
    def test_condenser_calcule_les_trous(self):
        noeuds = _communaute("a", 0, 3) + _communaute("b", 1, 3)
        noms_communautes = {0: "Travail", 1: "Maison"}

        from app.viz.analyse import condenser

        condense = condenser(noeuds, [], noms_communautes)

        assert len(condense.trous) == 1
        assert {condense.trous[0].sujet_a, condense.trous[0].sujet_b} == {"Travail", "Maison"}
