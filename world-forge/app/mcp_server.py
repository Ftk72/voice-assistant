from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.world.base import WorldGateway


def build_mcp(world: WorldGateway) -> FastMCP:
    """Outils MCP consommés par le client natif d'OpenWebUI (phase 6, ADR 0007)."""
    mcp = FastMCP(
        "world-forge",
        stateless_http=True,
        streamable_http_path="/",
        # La protection anti-DNS-rebinding du SDK n'accepte que localhost par défaut :
        # OpenWebUI arrive du réseau Docker avec Host « world:8300 » → 421. On garde
        # la protection (port publié sur 127.0.0.1) mais avec les hôtes légitimes.
        transport_security=TransportSecuritySettings(
            allowed_hosts=["world:8300", "127.0.0.1:8300", "localhost:8300", "testserver"]
        ),
    )

    @mcp.tool(
        description=(
            "Cherche sur le web une information que tu ne connais pas ou qui a pu changer "
            "(actualité, version d'un logiciel, fait récent). Renvoie des extraits avec leur "
            "source ; réponds ensuite en une ou deux phrases en citant ta source à l'oral "
            "(« d'après tel site… »). Ne lis jamais la liste brute ni les adresses complètes."
        )
    )
    async def web_search(query: str) -> str:
        results = await world.search(query)
        if not results:
            return f"Aucun résultat trouvé pour : {query}."
        lines = [
            f"- {result.title} ({result.url})\n  {result.snippet}" for result in results
        ]
        return "Extraits trouvés (à synthétiser en citant la source) :\n" + "\n".join(lines)

    @mcp.tool(
        description=(
            "Prévisions météo pour un lieu (« quel temps demain à Lyon ? »). "
            "days=1 pour aujourd'hui, 2 pour inclure demain, jusqu'à 7. "
            "Restitue oralement : conditions, minimale et maximale arrondies, pluie si notable."
        )
    )
    async def weather(place: str, days: int = 2) -> str:
        try:
            report = await world.weather(place, days=max(1, min(days, 7)))
        except LookupError as error:
            return str(error)
        lines = [
            f"- {day.day.isoformat()} : {day.description}, de {day.temp_min:.0f} à "
            f"{day.temp_max:.0f} degrés"
            + (
                f", {day.precipitation_probability} % de risque de pluie"
                if day.precipitation_probability is not None
                else ""
            )
            for day in report.days
        ]
        return f"Prévisions pour {report.place} :\n" + "\n".join(lines)

    @mcp.tool(
        description=(
            "Le briefing : dernières actualités des flux choisis par l'utilisateur "
            "(« quoi de neuf ? », « le briefing du matin »). Renvoie les titres par source ; "
            "fais-en un résumé parlé de quelques phrases, ne lis pas la liste."
        )
    )
    async def briefing() -> str:
        items = await world.headlines()
        if not items:
            return "Aucun flux configuré ou aucun élément récupéré."
        lines = [f"- [{item.feed}] {item.title}" + (f" — {item.summary}" if item.summary else "")
                 for item in items]
        return "Éléments du briefing (à résumer oralement) :\n" + "\n".join(lines)

    @mcp.tool(
        description=(
            "Lit une page web précise désignée par l'utilisateur (« lis-moi cet article », "
            "« résume cette page »). Renvoie le texte de la page ; lis-le ou résume-le selon "
            "la demande, en signalant si le texte a été tronqué."
        )
    )
    async def read_page(url: str) -> str:
        page = await world.read_page(url)
        suffix = "\n[Texte tronqué.]" if page.truncated else ""
        return f"{page.title}\n\n{page.text}{suffix}"

    return mcp
