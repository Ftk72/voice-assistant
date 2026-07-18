"""Récit du graphe mémoire (ticket wayfinder 0020) : condensé, prompt, adaptateur
factice, route /insight."""

from datetime import UTC, datetime

from app.insight.fake import GenerateurInsightFactice
from app.insight.prompt import construire_messages
from app.schemas import CondenseGraphe, GraphEdge, NoeudGraphe, Provenance, TrouCondense
from app.viz.analyse import condenser

_PROVENANCE = Provenance(source="conversation", name="test")


def _arete(source: str, target: str, invalide: bool = False) -> GraphEdge:
    return GraphEdge(
        source=source,
        target=target,
        text=f"{source}-{target}",
        provenance=_PROVENANCE,
        invalid_at=datetime.now(UTC) if invalide else None,
    )


class TestCondenser:
    def test_deux_communautes_et_un_pont(self):
        # Amas A : Léa-Judo-Karaté ; amas B : Max-Épinards ; Judo relie les deux
        # amas via un fait vers Max, ce qui en fait un pont.
        noeuds = [
            NoeudGraphe(nom="Léa", communaute=0, centralite=0.6),
            NoeudGraphe(nom="Judo", communaute=0, centralite=0.9),
            NoeudGraphe(nom="Karaté", communaute=0, centralite=0.3),
            NoeudGraphe(nom="Max", communaute=1, centralite=0.5),
            NoeudGraphe(nom="Épinards", communaute=1, centralite=0.2),
        ]
        aretes = [
            _arete("Léa", "Judo"),
            _arete("Léa", "Karaté"),
            _arete("Max", "Épinards"),
            _arete("Judo", "Max"),
            _arete("Léa", "Karaté", invalide=True),
        ]
        noms_communautes = {0: "Léa · Judo · Karaté", 1: "Max · Épinards"}

        condense = condenser(noeuds, aretes, noms_communautes)

        assert condense.nb_entites == 5
        assert condense.nb_faits == 5
        assert condense.nb_faits_obsoletes == 1
        assert [s.nom for s in condense.sujets] == ["Léa · Judo · Karaté", "Max · Épinards"]
        assert condense.sujets[0].taille == 3
        assert condense.sujets[1].taille == 2
        assert "Judo" in condense.ponts

    def test_graphe_vide(self):
        condense = condenser([], [], {})

        assert condense == CondenseGraphe(
            nb_entites=0, nb_faits=0, nb_faits_obsoletes=0, sujets=[], ponts=[]
        )

    def test_pas_plus_de_cinq_ponts(self):
        # 6 nœuds isolés dans 6 communautés différentes, tous reliés à un nœud
        # central pivot : tous les 6 sont des ponts, mais seuls 5 sont gardés.
        noeuds = [NoeudGraphe(nom="Pivot", communaute=0, centralite=1.0)]
        aretes = []
        for i in range(6):
            nom = f"Satellite{i}"
            noeuds.append(NoeudGraphe(nom=nom, communaute=i + 1, centralite=0.1))
            aretes.append(_arete("Pivot", nom))
        noms_communautes = {i: f"c{i}" for i in range(7)}

        condense = condenser(noeuds, aretes, noms_communautes)

        assert len(condense.ponts) == 5
        assert "Pivot" in condense.ponts  # centralité maximale : toujours en tête


class TestGenerateurInsightFactice:
    async def test_produit_un_paragraphe_non_vide_avec_le_premier_sujet(self):
        condense = CondenseGraphe(
            nb_entites=5,
            nb_faits=4,
            nb_faits_obsoletes=1,
            sujets=[{"nom": "Léa · Judo", "taille": 3}, {"nom": "Max", "taille": 2}],
            ponts=["Judo"],
        )

        paragraphe = await GenerateurInsightFactice().generer(condense)

        assert paragraphe.strip() != ""
        assert "Léa · Judo" in paragraphe
        assert "Judo" in paragraphe

    async def test_graphe_vide_renvoie_un_paragraphe_honnete(self):
        condense = CondenseGraphe(nb_entites=0, nb_faits=0, nb_faits_obsoletes=0)

        paragraphe = await GenerateurInsightFactice().generer(condense)

        assert paragraphe.strip() != ""


class TestConstruireMessages:
    def test_contient_les_sujets_et_demande_un_paragraphe(self):
        condense = CondenseGraphe(
            nb_entites=5,
            nb_faits=4,
            nb_faits_obsoletes=0,
            sujets=[{"nom": "Léa · Judo", "taille": 3}],
            ponts=["Judo"],
        )

        messages = construire_messages(condense)

        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        contenu = messages[1]["content"]
        assert "Léa · Judo" in contenu
        assert "Judo" in contenu
        assert "paragraphe" in contenu.lower()
        assert "liste" in (messages[0]["content"] + contenu).lower()

    def test_contient_les_angles_morts_quand_il_y_en_a(self):
        condense = CondenseGraphe(
            nb_entites=8,
            nb_faits=6,
            nb_faits_obsoletes=0,
            sujets=[{"nom": "Travail", "taille": 4}, {"nom": "Maison", "taille": 4}],
            ponts=[],
            trous=[
                TrouCondense(
                    communaute_a=1,
                    communaute_b=0,
                    sujet_a="Maison",
                    sujet_b="Travail",
                    nb_aretes=0,
                )
            ],
        )

        messages = construire_messages(condense)
        contenu = messages[1]["content"]

        assert "Maison" in contenu
        assert "Travail" in contenu
        assert "angle" in contenu.lower()
        assert "question" in (messages[0]["content"] + contenu).lower()

    def test_mentionne_l_absence_d_angle_mort_quand_il_n_y_en_a_pas(self):
        condense = CondenseGraphe(
            nb_entites=5, nb_faits=4, nb_faits_obsoletes=0, sujets=[], ponts=[], trous=[]
        )

        messages = construire_messages(condense)
        contenu = messages[1]["content"]

        assert "aucun angle mort notable" in contenu.lower()


class TestRouteInsight:
    def test_get_insight_renvoie_le_paragraphe_et_le_condense(self, client):
        client.post(
            "/episodes",
            json={"content": "Léa fait du Judo.", "source": "conversation", "name": "conv"},
        )
        import time

        deadline = time.monotonic() + 5
        payload = {"condense": {"nb_entites": 0}}
        while time.monotonic() < deadline and payload["condense"]["nb_entites"] == 0:
            payload = client.get("/insight").json()
            time.sleep(0.02)

        assert payload["insight"].strip() != ""
        assert payload["condense"]["nb_entites"] >= 1
