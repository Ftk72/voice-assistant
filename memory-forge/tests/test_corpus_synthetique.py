"""Le corpus synthétique garantit, par construction, chaque cas limite que la
viz devra savoir rendre (ticket wayfinder 0016) — ces tests sont le contrat."""

from collections import Counter, defaultdict

from app.graph.ontologie import TYPES_D_ENTITES
from scripts.corpus_synthetique import (
    CAS_FAUTIFS,
    COMMUNAUTE_PERIPHERIQUE,
    ENTITE_TOUT_OBSOLETE,
    NOEUDS_ISOLES,
    NOMS_A_RALLONGE,
    PONTS,
    TROU_STRUCTUREL,
    generer_corpus,
    preparer_lignes,
)


def test_le_corpus_est_deterministe():
    assert generer_corpus(graine=7) == generer_corpus(graine=7)


def test_les_communautes_ont_des_tailles_contrastees():
    corpus = generer_corpus()
    tailles = Counter(corpus.communaute_de.values())
    assert max(tailles.values()) >= 100, "il faut une communauté géante"
    assert min(tailles.values()) <= 4, "il faut une communauté minuscule"
    assert len(tailles) == 8


def test_le_volume_atteint_plusieurs_centaines_d_entites():
    corpus = generer_corpus()
    assert len(corpus.noeuds) >= 250


def test_chaque_pont_relie_bien_ses_deux_communautes():
    corpus = generer_corpus()
    for pont, origine, cible in PONTS:
        assert corpus.communaute_de[pont] == origine
        vers_cible = [
            a for a in corpus.aretes
            if pont in (a.source, a.target)
            and corpus.communaute_de.get(a.target if a.source == pont else a.source) == cible
        ]
        assert len(vers_cible) >= 3, f"{pont} doit ancrer plusieurs faits vers {cible}"


def test_le_trou_structurel_est_quasi_deconnecte():
    corpus = generer_corpus()
    gauche, droite = TROU_STRUCTUREL
    traversantes = [
        a for a in corpus.aretes
        if {corpus.communaute_de.get(a.source), corpus.communaute_de.get(a.target)}
        == {gauche, droite}
    ]
    assert len(traversantes) <= 1


def test_la_communaute_peripherique_ne_tient_qu_a_un_fil():
    corpus = generer_corpus()
    sortantes = [
        a for a in corpus.aretes
        if (corpus.communaute_de.get(a.source) == COMMUNAUTE_PERIPHERIQUE)
        != (corpus.communaute_de.get(a.target) == COMMUNAUTE_PERIPHERIQUE)
    ]
    assert len(sortantes) == 1


def test_les_noeuds_isoles_n_ont_aucune_arete():
    corpus = generer_corpus()
    assert len(NOEUDS_ISOLES) >= 5
    impliques = {a.source for a in corpus.aretes} | {a.target for a in corpus.aretes}
    for isole in NOEUDS_ISOLES:
        assert isole in corpus.noeuds
        assert isole not in impliques


def test_des_faits_obsoletes_en_masse():
    corpus = generer_corpus()
    obsoletes = [a for a in corpus.aretes if a.obsolete_depuis is not None]
    assert len(obsoletes) >= len(corpus.aretes) * 0.10
    for a in obsoletes:
        assert a.obsolete_depuis > a.valide_depuis


def test_l_entite_demenagement_est_tout_obsolete():
    corpus = generer_corpus()
    siens = [a for a in corpus.aretes if ENTITE_TOUT_OBSOLETE in (a.source, a.target)]
    assert siens, "l'entité déménagement doit exister et porter des faits"
    assert all(a.obsolete_depuis is not None for a in siens)


def test_les_deux_provenances_sont_presentes():
    corpus = generer_corpus()
    sources = {a.provenance_source for a in corpus.aretes}
    assert sources == {"conversation", "document"}
    assert all(a.provenance_nom for a in corpus.aretes)


def test_les_noms_a_rallonge_sont_relies():
    corpus = generer_corpus()
    impliques = {a.source for a in corpus.aretes} | {a.target for a in corpus.aretes}
    for nom in NOMS_A_RALLONGE:
        assert len(nom) > 35
        assert nom in impliques, "un nom à rallonge isolé ne testerait pas les étiquettes"


def test_aucune_arete_en_double_ni_boucle():
    corpus = generer_corpus()
    paires = [frozenset((a.source, a.target)) for a in corpus.aretes]
    assert len(paires) == len(set(paires))
    assert all(a.source != a.target for a in corpus.aretes)


def test_le_graphe_hors_isoles_est_connexe():
    corpus = generer_corpus()
    voisins = defaultdict(set)
    for a in corpus.aretes:
        voisins[a.source].add(a.target)
        voisins[a.target].add(a.source)
    depart = next(iter(voisins))
    vus = {depart}
    pile = [depart]
    while pile:
        for voisin in voisins[pile.pop()]:
            if voisin not in vus:
                vus.add(voisin)
                pile.append(voisin)
    assert vus == set(corpus.communaute_de), "toutes les communautés doivent se rejoindre"


def test_les_lignes_portent_les_champs_obligatoires_de_graphiti():
    """Impasse 2026-07-18 : l'index fulltext de Neo4j voit les arêtes
    synthétiques, et Graphiti valide chaque enregistrement en pydantic —
    sans group_id/created_at/name, toute recherche `/search` rend un 500."""
    episodes, noeuds, aretes = preparer_lignes(generer_corpus())
    for episode in episodes:
        assert episode["group_id"] == ""
        assert episode["cree"] is not None
        assert episode["valide"] is not None
        assert episode["source"] in {"message", "text"}
        assert episode["contenu"]
    for noeud in noeuds:
        assert noeud["group_id"] == ""
        assert noeud["cree"] is not None
    for arete in aretes:
        assert arete["group_id"] == ""
        assert arete["cree"] is not None
        assert arete["nom"] == "RELIE"
        assert len(arete["episodes"]) == 1


def test_preparer_lignes_est_deterministe():
    corpus = generer_corpus()
    assert preparer_lignes(corpus) == preparer_lignes(corpus)


def test_toutes_les_entites_ont_un_type_dans_la_liste_blanche():
    """Ticket wayfinder 0029 : le type devient un label Neo4j, réservé aux 8
    de l'ontologie — aucune entité du corpus ne doit en sortir."""
    _, noeuds, _ = preparer_lignes(generer_corpus())
    assert noeuds, "le corpus doit produire des nœuds"
    for noeud in noeuds:
        assert noeud["type"] in TYPES_D_ENTITES


def test_les_trois_cas_fautifs_sont_presents_avec_les_champs_obligatoires():
    """Les 3 cas fautifs volontaires (mauvaise orthographe, mauvais type, fait
    faux) doivent survivre à `preparer_lignes` avec les champs Graphiti
    obligatoires (impasse 2026-07-18) pour être corrigeables depuis /viz."""
    corpus = generer_corpus()
    _, noeuds, aretes = preparer_lignes(corpus)

    noms = {n["nom"] for n in noeuds}
    assert CAS_FAUTIFS["entite_mal_orthographiee"] in noms
    assert CAS_FAUTIFS["entite_mauvais_type"] in noms

    par_nom = {n["nom"]: n for n in noeuds}
    for cle in ("entite_mal_orthographiee", "entite_mauvais_type"):
        ligne = par_nom[CAS_FAUTIFS[cle]]
        assert ligne["type"] in TYPES_D_ENTITES
        assert ligne["group_id"] == ""
        assert ligne["cree"] is not None

    faits_faux = [a for a in aretes if a["fait"] == CAS_FAUTIFS["fait_faux_texte"]]
    assert len(faits_faux) == 1
    arete = faits_faux[0]
    assert {arete["source"], arete["target"]} == {
        CAS_FAUTIFS["fait_faux_source"], CAS_FAUTIFS["fait_faux_cible"]
    }
    assert arete["group_id"] == ""
    assert arete["cree"] is not None
    assert arete["nom"] == "RELIE"
    assert len(arete["episodes"]) == 1
