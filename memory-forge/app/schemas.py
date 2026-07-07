from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Source = Literal["conversation", "document"]


class EpisodeIn(BaseModel):
    """Unité d'ingestion : un échange de conversation daté ou un fragment de document."""

    content: str
    source: Source
    name: str


class Provenance(BaseModel):
    source: Source
    name: str


class Fact(BaseModel):
    """Une relation mémorisée, avec provenance et période de validité (cf. CONTEXT.md)."""

    text: str
    provenance: Provenance
    valid_at: datetime | None = None
    invalid_at: datetime | None = None


class SearchResponse(BaseModel):
    facts: list[Fact]


class GraphEdge(BaseModel):
    """Un fait vu comme arête entre deux entités (source == target : fait à une
    seule entité, affiché sur le nœud)."""

    source: str
    target: str
    text: str
    provenance: Provenance
    valid_at: datetime | None = None
    invalid_at: datetime | None = None


class GraphNeighborhood(BaseModel):
    """Voisinage navigable d'une entité — le contrat de la visualisation (phase 5)."""

    center: str
    nodes: list[str]
    edges: list[GraphEdge]


class NoeudGraphe(BaseModel):
    """Un nœud du graphe complet, enrichi pour la vue 3D (communauté = couleur,
    centralité = taille — cf. app/viz/analyse.py)."""

    nom: str
    communaute: int = 0
    centralite: float = 0.0


class GrapheComplet(BaseModel):
    """Le graphe entier (ou sa tranche la plus connectée), le contrat de la
    visualisation 3D type InfraNodus (ADR 0010 point 6, roadmap B1)."""

    noeuds: list[NoeudGraphe]
    aretes: list[GraphEdge]
    tronque: bool = False
