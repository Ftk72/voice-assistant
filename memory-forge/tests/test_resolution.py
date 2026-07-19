"""Résolution floue des mentions d'entités (ticket wayfinder 0028) : l'ancrage
anti-hallucination — les mentions du LLM se résolvent contre les vrais noms de
nœuds, en pur Python, sans LLM ni Neo4j."""

from app.interrogation.resolution import resoudre

NOMS = ["Léa", "Le club de pétanque", "Marc Dupont", "École Jules-Ferry"]


def test_le_nom_exact_se_resout_sur_lui_meme():
    resolues, non_resolues = resoudre(["Léa"], NOMS)
    assert [(r.mention, r.noeud) for r in resolues] == [("Léa", "Léa")]
    assert non_resolues == []


def test_la_casse_ne_compte_pas():
    resolues, _ = resoudre(["léa"], NOMS)
    assert resolues[0].noeud == "Léa"


def test_les_accents_ne_comptent_pas():
    resolues, _ = resoudre(["Lea"], NOMS)
    assert resolues[0].noeud == "Léa"


def test_la_sous_chaine_suffit():
    resolues, _ = resoudre(["pétanque"], NOMS)
    assert resolues[0].noeud == "Le club de pétanque"


def test_la_mention_peut_contenir_le_nom():
    """L'inverse : « Marc Dupont le voisin » contient le nom du nœud."""
    resolues, _ = resoudre(["Marc Dupont le voisin"], NOMS)
    assert resolues[0].noeud == "Marc Dupont"


def test_la_mention_inconnue_remonte_au_lieu_d_entrer_dans_la_requete():
    resolues, non_resolues = resoudre(["Zorglub"], NOMS)
    assert resolues == []
    assert non_resolues == ["Zorglub"]


def test_le_nom_exact_prime_sur_la_sous_chaine():
    """« Léa » ne doit pas s'ancrer sur un nom plus long qui la contiendrait."""
    resolues, _ = resoudre(["Léa"], ["Léandre", "Léa"])
    assert resolues[0].noeud == "Léa"


def test_plusieurs_mentions_gardent_l_ordre():
    resolues, non_resolues = resoudre(["lea", "Zorglub", "jules ferry"], NOMS)
    assert [r.noeud for r in resolues] == ["Léa", "École Jules-Ferry"]
    assert non_resolues == ["Zorglub"]
