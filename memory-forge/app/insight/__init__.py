"""Récit du graphe mémoire par le LLM local (ticket wayfinder 0020) : un port
(`base.GenerateurInsight`), un adaptateur factice et un adaptateur réel
llama.cpp, plus la logique de service partagée entre la route `/insight` et
l'outil MCP `raconter_memoire`."""

from app.graph.base import GraphMemory
from app.insight.base import GenerateurInsight
from app.schemas import CondenseGraphe, InsightReponse
from app.viz.analyse import condenser, enrichir, nommer_communautes

LIMITE_GRAPHE_INSIGHT = 500


async def calculer_condense(graph: GraphMemory) -> CondenseGraphe:
    """Graphe complet (sans filtre de provenance) → condensé, la même tranche
    de calcul pour la route `/insight` et l'outil MCP `raconter_memoire`."""
    graphe = await graph.graphe_complet(LIMITE_GRAPHE_INSIGHT)
    noms = [n.nom for n in graphe.noeuds]
    noeuds = enrichir(noms, graphe.aretes)
    noms_communautes = nommer_communautes(noeuds)
    return condenser(noeuds, graphe.aretes, noms_communautes)


async def raconter(graph: GraphMemory, generateur: GenerateurInsight) -> InsightReponse:
    """Condensé du graphe complet puis récit par le générateur fourni."""
    condense = await calculer_condense(graph)
    insight = await generateur.generer(condense)
    return InsightReponse(insight=insight, condense=condense)
