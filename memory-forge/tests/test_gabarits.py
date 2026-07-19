"""Les cinq gabarits Cypher écrits main et les garde-fous du repli libre
(ticket wayfinder 0028) — tout en pur Python, sans Neo4j."""

import pytest

from app.interrogation.gabarits import GABARITS, construire_requete
from app.interrogation.garde_fous import RequeteInterdite, borner

# --- Gabarits ---


def test_les_cinq_gabarits_existent():
    assert set(GABARITS) == {
        "faits_sur", "lien_entre", "lecture_temporelle", "autour_du_sujet", "compter"
    }


def test_chaque_gabarit_est_borne_et_en_lecture_seule():
    for nom, gabarit in GABARITS.items():
        assert "LIMIT" in gabarit.cypher, f"{nom} sans LIMIT"
        borner(gabarit.cypher)  # ne lève pas : aucune clause d'écriture


def test_faits_sur_parametre_l_entite():
    requete = construire_requete("faits_sur", {"entite": "Léa"})
    assert requete.parametres == {"entite": "Léa"}
    assert "$entite" in requete.cypher


def test_lien_entre_prend_deux_entites_et_le_plus_court_chemin():
    requete = construire_requete("lien_entre", {"entite_a": "Léa", "entite_b": "Marc"})
    assert requete.parametres == {"entite_a": "Léa", "entite_b": "Marc"}
    assert "shortestPath" in requete.cypher


def test_lecture_temporelle_ordonne_par_validite():
    requete = construire_requete("lecture_temporelle", {"entite": "Léa"})
    assert "ORDER BY" in requete.cypher and "valid_at" in requete.cypher


def test_autour_du_sujet_cherche_dans_les_faits_sans_resolution():
    requete = construire_requete("autour_du_sujet", {"sujet": "judo"})
    assert requete.parametres == {"sujet": "judo"}


def test_compter_accepte_un_sujet_optionnel():
    assert construire_requete("compter", {}).parametres == {"sujet": None}
    assert construire_requete("compter", {"sujet": "judo"}).parametres == {"sujet": "judo"}


def test_un_parametre_inconnu_est_ignore():
    requete = construire_requete("faits_sur", {"entite": "Léa", "furtif": "x"})
    assert "furtif" not in requete.parametres


def test_un_gabarit_inconnu_leve():
    with pytest.raises(KeyError):
        construire_requete("inexistant", {})


def test_les_parametres_entites_sont_declares():
    assert GABARITS["faits_sur"].parametres_entites == frozenset({"entite"})
    assert GABARITS["lien_entre"].parametres_entites == frozenset({"entite_a", "entite_b"})
    assert GABARITS["autour_du_sujet"].parametres_entites == frozenset()


# --- Garde-fous du repli Cypher libre ---


def test_une_lecture_simple_passe_et_recoit_un_limit():
    borne = borner("MATCH (n:Entity) RETURN n.name")
    assert borne.rstrip().endswith("LIMIT 100")


def test_un_limit_existant_est_conserve():
    borne = borner("MATCH (n:Entity) RETURN n.name LIMIT 5")
    assert borne.count("LIMIT") == 1


@pytest.mark.parametrize(
    "clause",
    [
        "CREATE (n:Entity {name: 'x'})",
        "MATCH (n) DELETE n",
        "MATCH (n) DETACH DELETE n",
        "MERGE (n:Entity {name: 'x'})",
        "MATCH (n) SET n.name = 'x'",
        "MATCH (n) REMOVE n.name",
        "DROP INDEX truc",
        "CALL db.labels()",
        "LOAD CSV FROM 'file:///x' AS ligne RETURN ligne",
        "MATCH (n) RETURN n; MATCH (m) DELETE m",
    ],
)
def test_les_clauses_d_ecriture_sont_rejetees(clause):
    with pytest.raises(RequeteInterdite):
        borner(clause)


def test_le_rejet_ignore_la_casse():
    with pytest.raises(RequeteInterdite):
        borner("match (n) delete n")


def test_un_nom_d_entite_contenant_un_mot_interdit_ne_declenche_pas():
    """« Roset » contient « SET » : seuls les mots entiers comptent."""
    borner("MATCH (n:Entity) WHERE n.name = 'Roset' RETURN n.name")
