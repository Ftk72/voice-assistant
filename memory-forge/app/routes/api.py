from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import FileResponse

from app.schemas import EpisodeIn, GrapheComplet, GraphNeighborhood, SearchResponse
from app.viz.analyse import enrichir

VIZ_PAGE = Path(__file__).resolve().parent.parent / "viz" / "index.html"
VENDOR_DIR = Path(__file__).resolve().parent.parent / "viz" / "vendor"

router = APIRouter()


@router.get("/viz", include_in_schema=False)
def viz_page() -> FileResponse:
    """Page de visualisation 3D du graphe complet (roadmap B1, ADR 0010 point 6)."""
    return FileResponse(VIZ_PAGE)


@router.get("/viz/vendor/{nom_fichier}", include_in_schema=False)
def viz_vendor(nom_fichier: str) -> FileResponse:
    """Sert les bibliothèques JS vendorées (3d-force-graph) — zéro CDN, souveraineté
    (ADR 0010 point 6). `nom_fichier` n'est jamais interpolé dans un chemin hors de
    `VENDOR_DIR` : FastAPI ne route ici que le segment final de l'URL."""
    chemin = (VENDOR_DIR / nom_fichier).resolve()
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
    return GrapheComplet(noeuds=noeuds, aretes=aretes, tronque=graphe.tronque)


@router.delete("/facts")
async def forget(entity: str, request: Request) -> dict[str, int]:
    """Oubli : suppression réelle (distincte de l'obsolescence, cf. CONTEXT.md)."""
    return {"forgotten": await request.app.state.graph.forget(entity)}
