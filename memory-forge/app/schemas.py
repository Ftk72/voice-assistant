from datetime import datetime
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

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
    uuid: str | None = None
    # Trace de correction manuelle (ticket wayfinder 0029) : posée par
    # `invalider_fait`/`annuler_invalidation`, jamais par l'extraction.
    corrige_le: datetime | None = None
    corrige_geste: str | None = None


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
    uuid: str | None = None
    type: str | None = None
    # Trace de correction manuelle (ticket wayfinder 0029) : posée par
    # `corriger_type`/`renommer_entite`, jamais par l'extraction Graphiti.
    corrige_le: datetime | None = None
    corrige_geste: str | None = None
    nom_precedent: str | None = None
    type_precedent: str | None = None


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


class RequeteCypher(BaseModel):
    """Une requête Cypher paramétrée, prête à exécuter — éditable et rejouable
    sans LLM côté /viz (ticket wayfinder 0028)."""

    cypher: str
    parametres: dict[str, str | int | None] = {}


class Aiguillage(BaseModel):
    """Le JSON rendu par l'unique appel LLM structuré (ticket 0028) : soit un
    gabarit nommé et ses paramètres, soit du Cypher libre (repli). C'est le
    début du monologue intérieur — il s'affiche tel quel dans /viz."""

    mentions: list[str] = []
    gabarit: str | None = None
    parametres: dict[str, str | None] = {}
    cypher: str | None = None


class MentionResolue(BaseModel):
    """Une mention d'entité extraite de la question, ancrée sur le vrai nom
    d'un nœud du graphe (résolution floue côté serveur, jamais par le LLM)."""

    mention: str
    noeud: str


class Monologue(BaseModel):
    """Le monologue intérieur façon LinkQ (ticket 0028) : tout ce que le canal
    a pensé et exécuté, montré à l'humain plutôt que caché."""

    aiguillage: Aiguillage | None = None  # None quand la requête est rejouée sans LLM
    resolues: list[MentionResolue] = []
    non_resolues: list[str] = []
    requete: RequeteCypher | None = None  # None si rien n'était exécutable
    resultats: list[dict] = []  # lignes vérité-terrain, brutes


class EtatVue(BaseModel):
    """Contrat partagé avec le pilotage LLM (ticket 0025) : l'état que /viz
    applique via la fonction JS unique `appliquerVue(etat)` — surlignage des
    nœuds cités et vol de caméra vers le focus."""

    surligner: list[str] = []
    focus: str | None = None


class ContexteInterrogation(BaseModel):
    """Contexte léger côté appelant (service sans état) : la question
    précédente et ses entités résolues, fournis par la réponse précédente."""

    question_precedente: str | None = None
    entites: list[str] = []


class InterrogationIn(BaseModel):
    """Corps de `POST /interroger` : une question en français, OU une requête
    déjà construite à rejouer sans LLM (édition dans le monologue)."""

    question: str | None = None
    requete: RequeteCypher | None = None
    contexte: ContexteInterrogation | None = None

    @model_validator(mode="after")
    def _question_ou_requete(self) -> "InterrogationIn":
        if self.question is None and self.requete is None:
            raise ValueError("il faut une question ou une requête à rejouer")
        return self


class InterrogationReponse(BaseModel):
    """Réponse de `POST /interroger` : la réponse française sourcée par le
    graphe (None en rejeu sans LLM), le monologue complet, et l'état de vue à
    appliquer côté /viz."""

    reponse: str | None
    monologue: Monologue
    vue: EtatVue
    contexte: ContexteInterrogation


class EtSiIn(BaseModel):
    """Corps de `POST /et-si` (ticket wayfinder 0030) : le panier de masques
    éphémères — noms d'entités et uuids de faits à masquer pour l'instant du
    recalcul, jamais persistés."""

    noeuds_masques: list[str] = []
    faits_masques: list[str] = []


class EtSiReponse(BaseModel):
    """Réponse de `POST /et-si` : le sous-graphe masqué ré-enrichi (communautés
    et centralité recalculées dessus), plus les deux condensés (réel et
    masqué) pour que /viz calcule le diff côté client."""

    graphe: GrapheComplet
    condense_reel: CondenseGraphe
    condense_masque: CondenseGraphe


class CorrectionTypeIn(BaseModel):
    """Corps de `POST /corrections/type` : corrige le type d'une entité mal
    extraite (ticket wayfinder 0029) — validé contre les 8 types de l'ontologie."""

    uuid: str
    type: str

    @field_validator("type")
    @classmethod
    def _type_dans_l_ontologie(cls, valeur: str) -> str:
        from app.graph.ontologie import TYPES_D_ENTITES

        if valeur not in TYPES_D_ENTITES:
            raise ValueError(
                f"type inconnu : {valeur!r} (attendu un de {sorted(TYPES_D_ENTITES)})"
            )
        return valeur


class CorrectionRenommageIn(BaseModel):
    """Corps de `POST /corrections/renommage` : corrige le nom d'une entité mal
    orthographiée. Les textes des faits déjà extraits restent intacts."""

    uuid: str
    nom: str

    @field_validator("nom")
    @classmethod
    def _nom_non_vide(cls, valeur: str) -> str:
        if not valeur.strip():
            raise ValueError("le nom ne peut pas être vide")
        return valeur


class CorrectionCibleIn(BaseModel):
    """Corps de `POST /corrections/invalidation` et `POST /corrections/annulation` :
    seule la cible (uuid du fait) est nécessaire."""

    uuid: str
