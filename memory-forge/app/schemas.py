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
    noms_communautes: dict[int, str] = {}


class SujetCondense(BaseModel):
    """Un sujet (communauté nommée) du condensé du graphe (ticket wayfinder 0020)."""

    nom: str
    taille: int


class TrouCondense(BaseModel):
    """Paire de communautés quasi pas reliées (ticket wayfinder 0021) — un angle
    mort de la mémoire, matière à question pour l'assistant."""

    communaute_a: int
    communaute_b: int
    sujet_a: str
    sujet_b: str
    nb_aretes: int


class CondenseGraphe(BaseModel):
    """Résumé statistique du graphe complet, préparé pour être raconté par le LLM
    local (ticket wayfinder 0020) — jamais de chiffre à inventer côté prompt,
    tout part d'ici."""

    nb_entites: int
    nb_faits: int
    nb_faits_obsoletes: int
    sujets: list[SujetCondense] = []
    ponts: list[str] = []
    trous: list[TrouCondense] = []


class InsightReponse(BaseModel):
    """Réponse de `GET /insight` : le paragraphe généré et le condensé qui l'a
    nourri, pour la transparence côté /viz."""

    insight: str
    condense: CondenseGraphe
