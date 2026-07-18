"""Le corpus synthétique garantit, par construction, chaque cas limite que la
viz devra savoir rendre (ticket wayfinder 0016) — ces tests sont le contrat."""

from collections import Counter, defaultdict

from scripts.corpus_synthetique import (
    COMMUNAUTE_PERIPHERIQUE,
    ENTITE_TOUT_OBSOLETE,
    NOEUDS_ISOLES,
    NOMS_A_RALLONGE,
    PONTS,
    TROU_STRUCTUREL,
    generer_corpus,
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
