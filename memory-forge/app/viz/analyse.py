"""Analyse en Python pur du graphe complet (aucune dépendance nouvelle, pas de networkx) :
détection de communautés par propagation d'étiquettes et centralité par degré. Enrichit
les nœuds de `GET /graph/complet` pour la vue 3D (communauté = couleur, centralité =
taille — ADR 0010 point 6, roadmap B1)."""

from app.schemas import GraphEdge, NoeudGraphe

_MAX_ITERATIONS = 20


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
