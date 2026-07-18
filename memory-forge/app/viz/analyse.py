"""Analyse en Python pur du graphe complet (aucune dépendance nouvelle, pas de networkx) :
détection de communautés par propagation d'étiquettes et centralité par degré. Enrichit
les nœuds de `GET /graph/complet` pour la vue 3D (communauté = couleur, centralité =
taille — ADR 0010 point 6, roadmap B1)."""

from app.schemas import CondenseGraphe, GraphEdge, NoeudGraphe, SujetCondense, TrouCondense

_MAX_ITERATIONS = 20
_MAX_PONTS = 5
_MAX_ARETES_TROU = 1
_TAILLE_MIN_COMMUNAUTE = 3
_MAX_TROUS = 3


def _adjacence(noeuds: list[str], aretes: list[tuple[str, str]]) -> dict[str, list[str]]:
    """Liste d'adjacence non orientée ; ignore les boucles (fait à une seule entité)."""
    adjacence: dict[str, list[str]] = {n: [] for n in noeuds}
    for source, cible in aretes:
        if source not in adjacence or cible not in adjacence or source == cible:
            continue
        adjacence[source].append(cible)
        adjacence[cible].append(source)
    return adjacence


def detecter_communautes(noeuds: list[str], aretes: list[tuple[str, str]]) -> dict[str, int]:
    """Propagation d'étiquettes déterministe : chaque nœud part avec sa propre étiquette
    (son nom), puis adopte à chaque tour l'étiquette majoritaire de ses voisins — l'ordre
    de parcours (alphabétique) et le départage des égalités (étiquette la plus petite)
    sont fixes, donc le résultat est reproductible d'un appel à l'autre."""
    ordre = sorted(noeuds)
    adjacence = _adjacence(ordre, aretes)
    etiquette = {n: n for n in ordre}

    for _ in range(_MAX_ITERATIONS):
        changement = False
        for noeud in ordre:
            voisins = adjacence[noeud]
            if not voisins:
                continue
            compte: dict[str, int] = {}
            for voisin in voisins:
                label = etiquette[voisin]
                compte[label] = compte.get(label, 0) + 1
            maximum = max(compte.values())
            meilleure = min(label for label, n in compte.items() if n == maximum)
            if meilleure != etiquette[noeud]:
                etiquette[noeud] = meilleure
                changement = True
        if not changement:
            break

    # Renumérote les étiquettes (chaînes) en petits entiers 0..k-1, par ordre de
    # première apparition dans l'ordre alphabétique — stable et lisible côté vue 3D.
    correspondance: dict[str, int] = {}
    resultat: dict[str, int] = {}
    for noeud in ordre:
        label = etiquette[noeud]
        if label not in correspondance:
            correspondance[label] = len(correspondance)
        resultat[noeud] = correspondance[label]
    return resultat


def centralite_degre(noeuds: list[str], aretes: list[tuple[str, str]]) -> dict[str, float]:
    """Degré normalisé par le maximum observé (0 = isolé, 1 = nœud le plus connecté)."""
    degre = dict.fromkeys(noeuds, 0)
    for source, cible in aretes:
        if source not in degre or cible not in degre or source == cible:
            continue
        degre[source] += 1
        degre[cible] += 1
    maximum = max(degre.values(), default=0)
    if maximum == 0:
        return dict.fromkeys(noeuds, 0.0)
    return {n: degre[n] / maximum for n in noeuds}


def nommer_communautes(noeuds: list[NoeudGraphe]) -> dict[int, str]:
    """Nom déterministe et gratuit (pas de LLM, ticket 0020 séparé) : les 3 entités
    les plus centrales de chaque communauté, jointes par ` · ` — l'égalité de
    centralité se départage par ordre alphabétique du nom, pour rester reproductible."""
    par_communaute: dict[int, list[NoeudGraphe]] = {}
    for noeud in noeuds:
        par_communaute.setdefault(noeud.communaute, []).append(noeud)
    return {
        communaute: " · ".join(
            n.nom
            for n in sorted(membres, key=lambda n: (-n.centralite, n.nom))[:3]
        )
        for communaute, membres in par_communaute.items()
    }


def enrichir(noms: list[str], aretes: list[GraphEdge]) -> list[NoeudGraphe]:
    """Construit les `NoeudGraphe` (communauté + centralité) pour la liste de noms
    fournie, à partir des arêtes du graphe complet."""
    paires = [(arete.source, arete.target) for arete in aretes]
    communautes = detecter_communautes(noms, paires)
    centralites = centralite_degre(noms, paires)
    return [
        NoeudGraphe(nom=nom, communaute=communautes[nom], centralite=centralites[nom])
        for nom in noms
    ]


def _detecter_ponts(noeuds: list[NoeudGraphe], aretes: list[GraphEdge]) -> list[str]:
    """Une entité est un pont si ses arêtes touchent au moins 2 communautés
    distinctes (la sienne comprise, via la communauté de chaque voisin) — définition
    héritée du ticket 0019. Renvoie les 5 premières, triées par nombre de
    communautés touchées décroissant, puis centralité décroissante, puis nom
    alphabétique — déterministe."""
    par_nom = {n.nom: n for n in noeuds}
    communautes_touchees: dict[str, set[int]] = {n.nom: {n.communaute} for n in noeuds}
    for arete in aretes:
        source, cible = par_nom.get(arete.source), par_nom.get(arete.target)
        if source is None or cible is None or source.nom == cible.nom:
            continue
        communautes_touchees[source.nom].add(cible.communaute)
        communautes_touchees[cible.nom].add(source.communaute)

    ponts = [nom for nom, communautes in communautes_touchees.items() if len(communautes) >= 2]
    ponts.sort(
        key=lambda nom: (
            -len(communautes_touchees[nom]),
            -par_nom[nom].centralite,
            nom,
        )
    )
    return ponts[:_MAX_PONTS]


def detecter_trous(
    noeuds: list[NoeudGraphe], aretes: list[GraphEdge], noms_communautes: dict[int, str]
) -> list[TrouCondense]:
    """Un « trou structurel » (ticket 0021) est une paire de communautés quasi
    pas reliées — au plus `_MAX_ARETES_TROU` arête inter-communautés entre
    elles — un angle mort de la mémoire, matière à question pour l'assistant.
    Ignore les communautés de moins de `_TAILLE_MIN_COMMUNAUTE` entités ou
    sans nom. Classées par produit des tailles décroissant, départagées
    alphabétiquement par `(sujet_a, sujet_b)` ; seules les `_MAX_TROUS`
    premières sont gardées."""
    tailles: dict[int, int] = {}
    for noeud in noeuds:
        tailles[noeud.communaute] = tailles.get(noeud.communaute, 0) + 1
    communautes_valables = sorted(
        c
        for c, taille in tailles.items()
        if taille >= _TAILLE_MIN_COMMUNAUTE and c in noms_communautes
    )

    par_nom = {n.nom: n for n in noeuds}
    compte_aretes: dict[tuple[int, int], int] = {}
    for arete in aretes:
        source, cible = par_nom.get(arete.source), par_nom.get(arete.target)
        if source is None or cible is None or source.nom == cible.nom:
            continue
        if source.communaute == cible.communaute:
            continue
        paire = (min(source.communaute, cible.communaute), max(source.communaute, cible.communaute))
        compte_aretes[paire] = compte_aretes.get(paire, 0) + 1

    trous = []
    for i, a in enumerate(communautes_valables):
        for b in communautes_valables[i + 1 :]:
            nb = compte_aretes.get((a, b), 0)
            if nb > _MAX_ARETES_TROU:
                continue
            nom_a, nom_b = noms_communautes[a], noms_communautes[b]
            if nom_a <= nom_b:
                sujet_a, sujet_b, communaute_a, communaute_b = nom_a, nom_b, a, b
            else:
                sujet_a, sujet_b, communaute_a, communaute_b = nom_b, nom_a, b, a
            trous.append(
                TrouCondense(
                    communaute_a=communaute_a,
                    communaute_b=communaute_b,
                    sujet_a=sujet_a,
                    sujet_b=sujet_b,
                    nb_aretes=nb,
                )
            )

    trous.sort(
        key=lambda t: (-(tailles[t.communaute_a] * tailles[t.communaute_b]), t.sujet_a, t.sujet_b)
    )
    return trous[:_MAX_TROUS]


def condenser(
    noeuds: list[NoeudGraphe], aretes: list[GraphEdge], noms_communautes: dict[int, str]
) -> CondenseGraphe:
    """Condense le graphe complet en un résumé statistique (ticket 0020), support
    du récit du LLM local : nombre d'entités/faits, sujets nommés triés par
    taille, entités-ponts. Graphe vide → condensé à zéros et listes vides."""
    tailles: dict[int, int] = {}
    for noeud in noeuds:
        tailles[noeud.communaute] = tailles.get(noeud.communaute, 0) + 1
    sujets = [
        SujetCondense(nom=noms_communautes[communaute], taille=taille)
        for communaute, taille in tailles.items()
        if communaute in noms_communautes
    ]
    sujets.sort(key=lambda s: (-s.taille, s.nom))

    return CondenseGraphe(
        nb_entites=len(noeuds),
        nb_faits=len(aretes),
        nb_faits_obsoletes=sum(1 for a in aretes if a.invalid_at is not None),
        sujets=sujets,
        ponts=_detecter_ponts(noeuds, aretes),
        trous=detecter_trous(noeuds, aretes, noms_communautes),
    )
