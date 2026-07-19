from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from app.graph.base import GraphMemory
from app.insight import raconter
from app.insight.base import GenerateurInsight
from app.interrogation import interroger
from app.interrogation.base import TraducteurQuestion
from app.interrogation.executeur import ExecuteurCypher
from app.schemas import InterrogationIn


def build_mcp(
    graph: GraphMemory,
    insight: GenerateurInsight,
    traducteur: TraducteurQuestion,
    executeur: ExecuteurCypher,
) -> FastMCP:
    """Outils MCP consommés par le client natif d'OpenWebUI (recall/forget, ADR 0005)."""
    mcp = FastMCP(
        "memory-forge",
        stateless_http=True,
        streamable_http_path="/",
        # La protection anti-DNS-rebinding du SDK n'accepte que localhost par défaut :
        # OpenWebUI arrive du réseau Docker avec Host « memory:8200 » → 421. On garde
        # la protection (port publié sur 127.0.0.1) mais avec les hôtes légitimes.
        transport_security=TransportSecuritySettings(
            allowed_hosts=["memory:8200", "127.0.0.1:8200", "localhost:8200", "testserver"]
        ),
    )

    @mcp.tool(
        description=(
            "Interroge la mémoire persistante de l'assistant. À utiliser quand l'utilisateur "
            "demande ce qu'il a déjà dit sur un sujet, une personne ou un événement passé "
            "(« qu'est-ce que je t'ai dit sur… »). Renvoie des faits datés avec leur source ; "
            "reformule-les oralement, ne lis pas la liste brute."
        )
    )
    async def recall(query: str) -> str:
        facts = await graph.search(query)
        if not facts:
            return f"Aucun souvenir trouvé au sujet de : {query}."
        lines = []
        for fact in facts:
            status = "obsolète" if fact.invalid_at else "actif"
            date = fact.valid_at.date().isoformat() if fact.valid_at else "date inconnue"
            lines.append(f"- {fact.text} ({status}, {date}, source : {fact.provenance.name})")
        return "Souvenirs trouvés :\n" + "\n".join(lines)

    @mcp.tool(
        description=(
            "Oublie définitivement tout ce que la mémoire contient sur une entité (personne, "
            "sujet…). Suppression réelle et irréversible : avant d'appeler cet outil, annonce "
            "à l'utilisateur ce qui va être oublié, et n'appelle qu'à sa demande explicite."
        )
    )
    async def forget(entity: str) -> str:
        count = await graph.forget(entity)
        if count == 0:
            return f"Rien à oublier : aucun fait lié à « {entity} »."
        return f"C'est oublié : {count} fait(s) concernant « {entity} » supprimé(s) définitivement."

    @mcp.tool(
        description=(
            "Raconte ce que la mémoire persistante de l'assistant sait dans l'ensemble : ses "
            "sujets dominants et les entités qui font le pont entre plusieurs d'entre eux. À "
            "utiliser quand l'utilisateur demande « que sait ta mémoire ? », « raconte-moi ta "
            "mémoire », ou toute question portant sur la mémoire dans son ensemble plutôt que "
            "sur un sujet précis (pour un sujet précis, utilise plutôt recall). Restitue ce "
            "paragraphe oralement, tel quel ou reformulé, ne le lis pas comme une liste."
        )
    )
    async def raconter_memoire() -> str:
        return (await raconter(graph, insight)).insight

    @mcp.tool(
        description=(
            "Pose une question précise à la mémoire persistante (« que sait-on de… », « quel "
            "est le lien entre X et Y », « depuis quand… », « combien de… ») : la question est "
            "traduite en requête exécutée sur le graphe réel, la réponse ne cite que ce qui y "
            "est trouvé. Restitue oralement la réponse, source comprise (« d'après N faits du "
            "graphe ») ; si rien n'est trouvé, dis-le franchement, n'invente jamais."
        )
    )
    async def interroger_memoire(question: str) -> str:
        resultat = await interroger(
            graph, traducteur, executeur, InterrogationIn(question=question)
        )
        nb_faits = len(resultat.monologue.resultats)
        if nb_faits == 0:
            return resultat.reponse or "Je n'ai rien trouvé dans le graphe à ce sujet."
        return f"{resultat.reponse} (d'après {nb_faits} fait(s) du graphe)"

    return mcp
