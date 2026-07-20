from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.gestionnaire import GestionnaireTaches
from app.schemas import Tache

_LIBELLES_STATUT = {
    "en_cours": "en cours",
    "terminee": "terminée",
    "echouee": "échouée",
    "annulee": "annulée",
}


def _resume_dernier_pas(tache: Tache) -> str:
    """Une phrase sur le dernier pas — jamais le journal ligne à ligne (les
    outils MCP sont dits à voix haute)."""
    if not tache.journal:
        return "Aucun pas exécuté pour l'instant."
    dernier = tache.journal[-1]
    if dernier.resultat.code_retour == 0:
        return "Le dernier pas s'est déroulé sans erreur."
    return f"Le dernier pas a échoué (code {dernier.resultat.code_retour})."


def _cible(gestionnaire: GestionnaireTaches, tache_id: str | None) -> Tache | None:
    if tache_id is not None:
        return gestionnaire.obtenir(tache_id)
    return gestionnaire.derniere_en_cours()


def build_mcp(gestionnaire: GestionnaireTaches) -> FastMCP:
    """Outils MCP de l'Action Forge, consommés par le Dialogue Forge (ADR 0013)."""
    mcp = FastMCP(
        "action-forge",
        stateless_http=True,
        streamable_http_path="/",
        # La protection anti-DNS-rebinding du SDK n'accepte que localhost par défaut :
        # le Dialogue Forge arrive du réseau Docker avec Host « action:8800 » → 421.
        transport_security=TransportSecuritySettings(
            allowed_hosts=["action:8800", "127.0.0.1:8800", "localhost:8800", "testserver"]
        ),
    )

    @mcp.tool(
        description=(
            "Confie une Tâche à faire — à utiliser quand l'utilisateur demande de *faire* "
            "quelque chose (créer un fichier, convertir, calculer) plutôt que de répondre. "
            "L'outil rend la main tout de suite : la Tâche travaille en fond et **sa fin "
            "sera annoncée toute seule**. Réponds juste que tu t'y mets, ne promets pas de "
            "résultat et n'attends pas."
        )
    )
    async def confier_tache(enonce: str) -> str:
        gestionnaire.confier(enonce)
        return "Je m'y mets."

    @mcp.tool(
        description=(
            "Point d'étape sur une Tâche en cours (« où en est la tâche ? »). Sans "
            "argument, vise la Tâche en cours la plus récente. Restitue oralement "
            "l'avancement en une phrase, ne lis jamais le journal ligne à ligne."
        )
    )
    async def ou_en_est_la_tache(tache_id: str | None = None) -> str:
        tache = _cible(gestionnaire, tache_id)
        if tache is None:
            return "Aucune tâche en cours."
        statut = _LIBELLES_STATUT.get(tache.statut, tache.statut)
        return f"Tâche {statut}. {_resume_dernier_pas(tache)}"

    @mcp.tool(
        description=(
            "Annule une Tâche en cours. Sans argument, vise la Tâche en cours la plus "
            "récente (l'utilisateur ne dit jamais un identifiant à voix haute)."
        )
    )
    async def annuler_tache(tache_id: str | None = None) -> str:
        tache = _cible(gestionnaire, tache_id)
        if tache is None:
            return "Aucune tâche en cours."
        await gestionnaire.annuler(tache.id)
        return "Tâche annulée."

    return mcp
