from datetime import datetime, time, timedelta

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.store.base import AgendaStore
from app.timers import TimerBoard


def build_mcp(store: AgendaStore, timers: TimerBoard) -> FastMCP:
    """Outils MCP consommés par le client natif d'OpenWebUI (phases 3+5)."""
    mcp = FastMCP(
        "time-forge",
        stateless_http=True,
        streamable_http_path="/",
        # La protection anti-DNS-rebinding du SDK n'accepte que localhost par défaut :
        # OpenWebUI arrive du réseau Docker avec Host « time:8400 » → 421. On garde
        # la protection (port publié sur 127.0.0.1) mais avec les hôtes légitimes.
        transport_security=TransportSecuritySettings(
            allowed_hosts=["time:8400", "127.0.0.1:8400", "localhost:8400", "testserver"]
        ),
    )

    @mcp.tool(
        description=(
            "Crée un événement dans l'agenda de l'utilisateur. Sert aussi aux rappels "
            "(« rappelle-moi mercredi d'appeler le dentiste ») : un rappel est un événement "
            "avec announce_lead_minutes=0. Pour un rendez-vous, mets un préavis si demandé "
            "(« préviens-moi une heure avant » : announce_lead_minutes=60), sinon laisse vide. "
            "`when` en ISO 8601 local (2026-07-08T15:00). Confirme oralement la date en clair."
        )
    )
    async def create_event(
        title: str, when: str, announce_lead_minutes: int | None = None
    ) -> str:
        from app.schemas import EventIn

        event = await store.add(
            EventIn(
                title=title,
                when=datetime.fromisoformat(when),
                announce_lead_minutes=announce_lead_minutes,
            )
        )
        announced = (
            "sans annonce"
            if event.announce_lead_minutes is None
            else f"annoncé {event.announce_lead_minutes} min avant"
            if event.announce_lead_minutes
            else "annoncé à l'heure dite"
        )
        return (
            f"Noté (id {event.id}) : « {event.title} » "
            f"le {event.when:%A %d %B à %H:%M}, {announced}."
        )

    @mcp.tool(
        description=(
            "Liste les événements de l'agenda (« qu'est-ce que j'ai demain ? »). "
            "`day` en ISO (2026-07-08) pour un jour précis ; sans argument : les 7 prochains "
            "jours. Restitue oralement, ne lis pas les identifiants sauf pour une suppression."
        )
    )
    async def list_events(day: str | None = None) -> str:
        if day:
            start = datetime.combine(datetime.fromisoformat(day).date(), time.min)
            end = start + timedelta(days=1)
        else:
            start = datetime.now()
            end = start + timedelta(days=7)
        events = await store.list_between(start, end)
        if not events:
            return "Rien à l'agenda sur cette période."
        lines = [f"- {event.when:%A %d %B %H:%M} : {event.title} (id {event.id})"
                 for event in events]
        return "À l'agenda :\n" + "\n".join(lines)

    @mcp.tool(
        description=(
            "Supprime un événement de l'agenda. Retrouve d'abord son id via list_events, "
            "et confirme à l'utilisateur ce qui a été supprimé."
        )
    )
    async def delete_event(event_id: str) -> str:
        if await store.delete(event_id):
            return "Événement supprimé."
        return f"Aucun événement avec l'id {event_id}."

    @mcp.tool(
        description=(
            "Démarre un minuteur (« mets un minuteur pâtes de 8 minutes » : "
            "label='pâtes', seconds=480). Précis à la seconde ; une annonce vocale "
            "part à l'échéance. Relancer un label existant le remet à zéro."
        )
    )
    async def set_timer(label: str, seconds: int) -> str:
        timer = timers.start(label, seconds)
        return f"Minuteur « {timer.label} » lancé, échéance à {timer.ends_at:%H:%M:%S}."

    @mcp.tool(description="Annule un minuteur en cours, désigné par son étiquette.")
    async def cancel_timer(label: str) -> str:
        if timers.cancel(label):
            return f"Minuteur « {label} » annulé."
        return f"Aucun minuteur « {label} » en cours."

    @mcp.tool(
        description="Liste les minuteurs en cours avec le temps restant (« il reste combien ? »)."
    )
    async def list_timers() -> str:
        active = timers.active()
        if not active:
            return "Aucun minuteur en cours."
        now = datetime.now()
        lines = [
            f"- {timer.label} : encore {max(0, int((timer.ends_at - now).total_seconds()))} s"
            for timer in active
        ]
        return "Minuteurs en cours :\n" + "\n".join(lines)

    return mcp
