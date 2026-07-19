import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.graph.base import GraphMemory
from app.graph.fake import InMemoryGraph
from app.ingest.watcher import DocumentWatcher
from app.insight.base import GenerateurInsight
from app.insight.fake import GenerateurInsightFactice
from app.interrogation.base import TraducteurQuestion
from app.interrogation.executeur import ExecuteurCypher, ExecuteurCypherFactice
from app.interrogation.fake import TraducteurQuestionFactice
from app.mcp_server import build_mcp
from app.routes.api import router
from app.schemas import EpisodeIn

logger = logging.getLogger(__name__)


def build_graph(settings: Settings) -> GraphMemory:
    if settings.backend == "graphiti":
        from app.graph.graphiti import GraphitiMemory

        return GraphitiMemory(settings)
    return InMemoryGraph()


def build_generateur_insight(settings: Settings) -> GenerateurInsight:
    if settings.insight_backend == "openai":
        from app.insight.openai_compat import GenerateurInsightOpenAI

        return GenerateurInsightOpenAI(settings.llm_base_url)
    return GenerateurInsightFactice()


def build_traducteur(settings: Settings) -> TraducteurQuestion:
    if settings.interrogation_backend == "openai":
        from app.interrogation.openai_compat import TraducteurQuestionOpenAI

        return TraducteurQuestionOpenAI(settings.llm_base_url)
    return TraducteurQuestionFactice()


def build_executeur(settings: Settings) -> ExecuteurCypher:
    """L'exécuteur suit le backend graphe : graphiti → le vrai Neo4j de la
    stack, sinon le factice (le canal d'interrogation ne trouve alors rien)."""
    if settings.backend == "graphiti":
        from app.interrogation.executeur_neo4j import ExecuteurCypherNeo4j

        return ExecuteurCypherNeo4j(settings)
    return ExecuteurCypherFactice()


async def extraction_worker(queue: asyncio.Queue[EpisodeIn], graph: GraphMemory) -> None:
    """Consomme la file d'épisodes un par un — l'extraction différée de l'ADR 0005."""
    while True:
        episode = await queue.get()
        try:
            await graph.add_episode(episode)
            logger.info("Épisode intégré : %s (%s)", episode.name, episode.source)
        except Exception:
            logger.exception("Échec d'intégration de l'épisode %s", episode.name)
        finally:
            queue.task_done()


async def watch_documents(
    watcher: DocumentWatcher, queue: asyncio.Queue[EpisodeIn], poll_seconds: float
) -> None:
    """Polling du dossier documents/ ; les épisodes rejoignent la même file
    que les conversations (extraction différée)."""
    while True:
        try:
            for episode in await asyncio.to_thread(watcher.scan_once):
                queue.put_nowait(episode)
        except Exception:
            logger.exception("Échec du scan du dossier documents")
        await asyncio.sleep(poll_seconds)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    graph = build_graph(settings)
    insight = build_generateur_insight(settings)
    traducteur = build_traducteur(settings)
    executeur = build_executeur(settings)
    mcp = build_mcp(graph, insight, traducteur, executeur)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        await app.state.graph.initialize()
        tasks = [asyncio.create_task(extraction_worker(app.state.queue, app.state.graph))]
        if settings.documents_dir is not None:
            watcher = DocumentWatcher(settings.documents_dir)
            tasks.append(
                asyncio.create_task(
                    watch_documents(watcher, app.state.queue, settings.documents_poll_seconds)
                )
            )
        async with mcp.session_manager.run():
            yield
        for task in tasks:
            task.cancel()

    app = FastAPI(title="Memory Forge", lifespan=lifespan)
    app.state.settings = settings
    app.state.graph = graph
    app.state.insight = insight
    app.state.traducteur = traducteur
    app.state.executeur = executeur
    app.state.queue = asyncio.Queue()
    app.include_router(router)
    app.mount("/mcp", mcp.streamable_http_app())
    return app
