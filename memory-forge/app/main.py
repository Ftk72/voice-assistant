import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.graph.base import GraphMemory
from app.graph.fake import InMemoryGraph
from app.mcp_server import build_mcp
from app.routes.api import router
from app.schemas import EpisodeIn

logger = logging.getLogger(__name__)


def build_graph(settings: Settings) -> GraphMemory:
    if settings.backend == "graphiti":
        from app.graph.graphiti import GraphitiMemory

        return GraphitiMemory(settings)
    return InMemoryGraph()


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


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    graph = build_graph(settings)
    mcp = build_mcp(graph)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        worker = asyncio.create_task(extraction_worker(app.state.queue, app.state.graph))
        async with mcp.session_manager.run():
            yield
        worker.cancel()

    app = FastAPI(title="Memory Forge", lifespan=lifespan)
    app.state.settings = settings
    app.state.graph = graph
    app.state.queue = asyncio.Queue()
    app.include_router(router)
    app.mount("/mcp", mcp.streamable_http_app())
    return app
