from mcp.server.fastmcp import FastMCP

from app.actions.base import ActionRunner
from app.catalog import Action


def build_mcp(catalog: dict[str, Action], runner: ActionRunner) -> FastMCP:
    """Outils MCP consommés par le client natif d'OpenWebUI (phase 4).
    Le Pont n'expose que la liste blanche : jamais un shell, jamais de commande
    arbitraire (ADR 0008)."""
    mcp = FastMCP("host-bridge", stateless_http=True, streamable_http_path="/")

    @mcp.tool(
        description=(
            "Liste les actions que l'utilisateur a mises dans son catalogue (ouvrir une "
            "application, piloter la musique, régler le volume…). Propose-les à l'utilisateur "
            "avec leurs descriptions ; ne restitue pas de détails techniques. C'est la seule "
            "chose que l'assistant peut faire sur la machine : rien hors de cette liste."
        )
    )
    def list_actions() -> str:
        if not catalog:
            return "Le catalogue d'actions est vide."
        lines = [f"- {action.name} : {action.description}" for action in catalog.values()]
        return "Actions disponibles :\n" + "\n".join(lines)

    @mcp.tool(
        description=(
            "Exécute une action du catalogue, désignée par son `name` (retrouvé via "
            "list_actions). N'exécute qu'à la demande claire de l'utilisateur, puis confirme "
            "oralement ce qui a été lancé. Un nom hors catalogue est refusé sans rien exécuter : "
            "seule la liste blanche existe."
        )
    )
    def run_action(name: str) -> str:
        action = catalog.get(name)
        if action is None:
            return f"« {name} » n'est pas dans la liste blanche : je ne peux pas l'exécuter."
        return runner.run(action)

    return mcp
