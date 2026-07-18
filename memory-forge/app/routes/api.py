from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from app.insight import raconter
from app.schemas import EpisodeIn, GrapheComplet, GraphNeighborhood, InsightReponse, SearchResponse
from app.viz.analyse import enrichir, nommer_communautes

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
    noms = [n.nom for n in graphe.noeuds]
    if provenance is not None:
        aretes = [a for a in aretes if a.provenance.source == provenance]
        relies = {a.source for a in aretes} | {a.target for a in aretes}
        noms = [n for n in noms if n in relies]
    noeuds = enrichir(noms, aretes)
    noms_communautes = nommer_communautes(noeuds)
    return GrapheComplet(
        noeuds=noeuds, aretes=aretes, tronque=graphe.tronque, noms_communautes=noms_communautes
    )


@router.get("/insight", response_model=InsightReponse)
async def insight(request: Request) -> InsightReponse:
    """Récit du graphe mémoire par le LLM local (ticket wayfinder 0020) : un
    paragraphe en français, plus le condensé qui l'a nourri (transparence côté
    /viz). Graphe complet sans filtre de provenance, même tranche que le
    condensé de l'outil MCP `raconter_memoire`."""
    return await raconter(request.app.state.graph, request.app.state.insight)


@router.delete("/facts")
async def forget(entity: str, request: Request) -> dict[str, int]:
    """Oubli : suppression réelle (distincte de l'obsolescence, cf. CONTEXT.md)."""
    return {"forgotten": await request.app.state.graph.forget(entity)}
