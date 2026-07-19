from abc import ABC, abstractmethod

from app.schemas import EpisodeIn, Fact, GrapheComplet, GraphNeighborhood


class CibleIntrouvable(Exception):
    """L'uuid visé par une correction (nœud ou fait) n'existe pas dans le graphe."""


class CorrectionRefusee(Exception):
    """Correction refusée : typiquement l'annulation d'une invalidation qui n'est
    pas d'origine manuelle (apprise par Graphiti, donc intouchable)."""


class GraphMemory(ABC):
    """Port du graphe de mémoire, calqué sur les scénarios de docs/ACCEPTANCE-MEMOIRE.md
    (et non sur l'API de Graphiti) : l'implémentation est interchangeable sans toucher
    à la Filter OpenWebUI ni au serveur MCP."""

    async def initialize(self) -> None:  # noqa: B027 — hook volontairement no-op par défaut
        """Préparation unique au démarrage (index, contraintes…) — no-op par défaut."""

    @abstractmethod
    async def add_episode(self, episode: EpisodeIn) -> None:
        """Extrait les faits de l'épisode et les intègre au graphe (résolution d'entités,
        invalidation des faits contredits)."""

    @abstractmethod
    async def search(self, query: str) -> list[Fact]:
        """Faits pertinents pour la requête, faits actifs d'abord."""

    @abstractmethod
    async def forget(self, entity: str) -> int:
        """Oubli : suppression réelle des faits liés à l'entité. Renvoie le nombre supprimé."""

    @abstractmethod
    async def neighborhood(self, entity: str, depth: int = 1) -> GraphNeighborhood:
        """Voisinage d'une entité, étendu de proche en proche jusqu'à `depth` sauts —
        alimente la visualisation (scénario visualisation d'ACCEPTANCE-MEMOIRE.md)."""

    @abstractmethod
    async def graphe_complet(self, limite: int = 500) -> GrapheComplet:
        """Le graphe entier (nœuds + arêtes = faits, provenance et validité comprises).
        Si le graphe dépasse `limite` nœuds, garde les plus connectés (degré décroissant)
        et les arêtes qui les relient entre eux — jamais d'omission silencieuse des faits
        obsolètes (invalid_at non nul), seulement marqués. Alimente la vue 3D (ADR 0010
        point 6, roadmap B1) ; l'enrichissement communauté/centralité vit dans
        app/viz/analyse.py, pas dans le port."""

    @abstractmethod
    async def corriger_type(self, uuid: str, type_: str) -> None:
        """Corrige le type (mal extrait) d'une entité — pose `type`, trace
        `type_precedent`/`corrige_le`/`corrige_geste="type"`. `CibleIntrouvable`
        si l'uuid est inconnu (ticket wayfinder 0029)."""

    @abstractmethod
    async def invalider_fait(self, uuid: str) -> None:
        """Invalide un fait faux dès son origine (erreur d'extraction, pas
        obsolescence) : `invalid_at = valid_at` (repli `created_at`). Trace
        `corrige_geste="invalidation"`. Jamais de suppression physique.
        `CibleIntrouvable` si l'uuid est inconnu."""

    @abstractmethod
    async def renommer_entite(self, uuid: str, nom: str) -> None:
        """Renomme une entité mal orthographiée ; trace `nom_precedent`/
        `corrige_geste="renommage"`. Les textes des faits (`r.fact`) restent
        INTACTS (citations historiques). `CibleIntrouvable` si l'uuid est
        inconnu."""

    @abstractmethod
    async def annuler_invalidation(self, uuid: str) -> None:
        """Annule une invalidation manuelle (remet `invalid_at` à null et efface
        la trace), SEULEMENT si la trace porte `corrige_geste == "invalidation"` :
        les invalidations apprises par Graphiti sont intouchables — sinon
        `CorrectionRefusee`. `CibleIntrouvable` si l'uuid est inconnu."""
