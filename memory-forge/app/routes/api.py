from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from app.graph.base import CibleIntrouvable, CorrectionRefusee
from app.insight import raconter
from app.interrogation import interroger
from app.interrogation.garde_fous import RequeteInterdite
from app.schemas import (
    CorrectionCibleIn,
    CorrectionRenommageIn,
    CorrectionTypeIn,
    EpisodeIn,
    EtSiIn,
    EtSiReponse,
    GrapheComplet,
    GraphNeighborhood,
    InsightReponse,
    InterrogationIn,
    InterrogationReponse,
    SearchResponse,
)
from app.viz.analyse import condenser, enrichir, masquer, nommer_communautes

LIMITE_GRAPHE_ET_SI = 500

VIZ_PAGE = Path(__file__).resolve().parent.parent / "viz" / "index.html"
VENDOR_DIR = Path(__file__).resolve().parent.parent / "viz" / "vendor"

router = APIRouter()


@router.get("/viz", include_in_schema=False)
def viz_page() -> FileResponse:
    """Page de visualisation 3D du graphe complet (roadmap B1, ADR 0010 point 6)."""
    return FileResponse(VIZ_PAGE)


@router.get("/viz/vendor/{chemin_relatif:path}", include_in_schema=False)
def viz_vendor(chemin_relatif: str) -> FileResponse:
    """Sert les bibliothèques JS vendorées (3d-force-graph, three.js + addons,
    three-spritetext) — zéro CDN, souveraineté (ADR 0010 point 6). `:path` accepte
    les sous-dossiers (les modules three.js s'importent entre eux par chemin
    relatif) ; `chemin_relatif` n'est jamais interpolé hors de `VENDOR_DIR` — le
    `.resolve()` normalise les `..` avant la vérification d'appartenance."""
    chemin = (VENDOR_DIR / chemin_relatif).resolve()
    if VENDOR_DIR not in chemin.parents or not chemin.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(chemin, media_type="application/javascript")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/episodes", status_code=202)
def enqueue_episode(episode: EpisodeIn, request: Request) -> dict[str, str]:
    """202 immédiat : la capture ne doit jamais bloquer OpenWebUI.
    L'extraction se fait dans la file, en différé."""
    request.app.state.queue.put_nowait(episode)
    return {"status": "queued"}


@router.get("/search", response_model=SearchResponse)
async def search(q: str, request: Request) -> SearchResponse:
    return SearchResponse(facts=await request.app.state.graph.search(q))


@router.get("/graph", response_model=GraphNeighborhood)
async def graph(
    entity: str, request: Request, depth: int = Query(default=1, ge=1, le=3)
) -> GraphNeighborhood:
    """Voisinage navigable d'une entité — consommé par la page /viz (phase 5)."""
    return await request.app.state.graph.neighborhood(entity, depth=depth)


@router.get("/graph/complet", response_model=GrapheComplet)
async def graphe_complet(
    request: Request,
    limite: int = Query(default=500, ge=1, le=5000),
    provenance: Literal["conversation", "document"] | None = None,
) -> GrapheComplet:
    """Le graphe entier, enrichi (communauté, centralité) — alimente la vue 3D
    (roadmap B1). Les faits obsolètes (invalid_at non nul) sont toujours inclus,
    jamais omis silencieusement : la page les estompe ou les masque à l'affichage.
    `provenance` filtre les arêtes ; les nœuds qu'elle isole disparaissent avec elles."""
    graphe = await request.app.state.graph.graphe_complet(limite)
    aretes = graphe.aretes
    noeuds_source = graphe.noeuds
    if provenance is not None:
        aretes = [a for a in aretes if a.provenance.source == provenance]
        relies = {a.source for a in aretes} | {a.target for a in aretes}
        noeuds_source = [n for n in noeuds_source if n.nom in relies]
    noeuds = enrichir(noeuds_source, aretes)
    noms_communautes = nommer_communautes(noeuds)
    return GrapheComplet(
        noeuds=noeuds, aretes=aretes, tronque=graphe.tronque, noms_communautes=noms_communautes
    )


@router.post("/et-si", response_model=EtSiReponse)
async def et_si(panier: EtSiIn, request: Request) -> EtSiReponse:
    """Contrefactuel « et si ? » (ticket wayfinder 0030) : masque des entités et
    des faits (panier éphémère, jamais persisté — aucune écriture dans le
    graphe) et recalcule communautés/centralité/condensé sur le sous-graphe
    obtenu, pour comparer à l'analyse réelle. Même tranche que `/insight`
    (500 nœuds les plus connectés) ; l'insight LLM n'est pas rejoué ici — trop
    lent pour un geste interactif, le diff déterministe des condensés suffit."""
    graphe = await request.app.state.graph.graphe_complet(LIMITE_GRAPHE_ET_SI)

    noeuds_reels = enrichir(graphe.noeuds, graphe.aretes)
    noms_communautes_reel = nommer_communautes(noeuds_reels)
    condense_reel = condenser(noeuds_reels, graphe.aretes, noms_communautes_reel)

    noeuds_masques, aretes_masquees = masquer(
        graphe.noeuds, graphe.aretes, panier.noeuds_masques, panier.faits_masques
    )
    noeuds_enrichis = enrichir(noeuds_masques, aretes_masquees)
    noms_communautes_masque = nommer_communautes(noeuds_enrichis)
    condense_masque = condenser(noeuds_enrichis, aretes_masquees, noms_communautes_masque)

    return EtSiReponse(
        graphe=GrapheComplet(
            noeuds=noeuds_enrichis,
            aretes=aretes_masquees,
            tronque=graphe.tronque,
            noms_communautes=noms_communautes_masque,
        ),
        condense_reel=condense_reel,
        condense_masque=condense_masque,
    )


@router.get("/insight", response_model=InsightReponse)
async def insight(request: Request) -> InsightReponse:
    """Récit du graphe mémoire par le LLM local (ticket wayfinder 0020) : un
    paragraphe en français, plus le condensé qui l'a nourri (transparence côté
    /viz). Graphe complet sans filtre de provenance, même tranche que le
    condensé de l'outil MCP `raconter_memoire`."""
    return await raconter(request.app.state.graph, request.app.state.insight)


@router.post("/interroger", response_model=InterrogationReponse)
async def interroger_route(demande: InterrogationIn, request: Request) -> InterrogationReponse:
    """Interroger la mémoire sans halluciner (ticket wayfinder 0028, modèle
    LinkQ) : question française → requête visible et exécutée sur le graphe →
    réponse sourcée + monologue intérieur + état de vue pour /viz. Avec
    `requete` au lieu de `question` : rejeu direct, sans LLM."""
    try:
        return await interroger(
            request.app.state.graph,
            request.app.state.traducteur,
            request.app.state.executeur,
            demande,
        )
    except RequeteInterdite as erreur:
        raise HTTPException(status_code=400, detail=str(erreur)) from erreur


@router.delete("/facts")
async def forget(entity: str, request: Request) -> dict[str, int]:
    """Oubli : suppression réelle (distincte de l'obsolescence, cf. CONTEXT.md)."""
    return {"forgotten": await request.app.state.graph.forget(entity)}


@router.post("/corrections/type")
async def corriger_type(corps: CorrectionTypeIn, request: Request) -> dict[str, str]:
    """Corrige le type d'une entité mal extraite (ticket wayfinder 0029) —
    correction ciblée depuis /viz, pas un éditeur de graphe : le type doit être
    l'un des 8 de l'ontologie (validé côté schéma)."""
    try:
        await request.app.state.graph.corriger_type(corps.uuid, corps.type)
    except CibleIntrouvable as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur
    return {"status": "ok"}


@router.post("/corrections/invalidation")
async def invalider_fait(corps: CorrectionCibleIn, request: Request) -> dict[str, str]:
    """Invalide un fait faux dès son origine (erreur d'extraction, pas
    obsolescence) — jamais de suppression physique (ticket wayfinder 0029)."""
    try:
        await request.app.state.graph.invalider_fait(corps.uuid)
    except CibleIntrouvable as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur
    return {"status": "ok"}


@router.post("/corrections/renommage")
async def renommer_entite(corps: CorrectionRenommageIn, request: Request) -> dict[str, str]:
    """Renomme une entité mal orthographiée (ticket wayfinder 0029) ; les textes
    des faits déjà extraits restent intacts (citations historiques) — pas de
    fusion de doublons, hors périmètre."""
    try:
        await request.app.state.graph.renommer_entite(corps.uuid, corps.nom)
    except CibleIntrouvable as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur
    return {"status": "ok"}


@router.post("/corrections/annulation")
async def annuler_invalidation(corps: CorrectionCibleIn, request: Request) -> dict[str, str]:
    """Annule une invalidation manuelle (geste de correction) — jamais une
    invalidation apprise par Graphiti, intouchable (ticket wayfinder 0029)."""
    try:
        await request.app.state.graph.annuler_invalidation(corps.uuid)
    except CibleIntrouvable as erreur:
        raise HTTPException(status_code=404, detail=str(erreur)) from erreur
    except CorrectionRefusee as erreur:
        raise HTTPException(status_code=409, detail=str(erreur)) from erreur
    return {"status": "ok"}
