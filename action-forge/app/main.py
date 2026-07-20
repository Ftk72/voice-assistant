from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.annonce.base import Annonceur
from app.annonce.journal import AnnonceurJournal
from app.atelier.base import Atelier
from app.atelier.fake import AtelierFactice
from app.boucle import BoucleCodeAct
from app.config import Settings
from app.gestionnaire import GestionnaireTaches
from app.llm.base import MoteurLLM
from app.llm.factice import MoteurLLMFactice
from app.mcp_server import build_mcp
from app.routes import router
from app.routes_atelier import router as router_atelier


def build_atelier_factory(settings: Settings) -> Callable[[], Atelier]:
    if settings.atelier_backend == "docker":
        from app.atelier.docker import AtelierDocker

        return lambda: AtelierDocker(settings)
    return AtelierFactice


def build_llm(settings: Settings) -> MoteurLLM:
    if settings.llm_backend == "openai":
        from app.llm.openai_compat import MoteurLLMOpenAI

        return MoteurLLMOpenAI(settings)
    return MoteurLLMFactice()


def build_annonceur(settings: Settings) -> Annonceur:
    if settings.annonceur == "pont_hote":
        from app.annonce.pont_hote import AnnonceurPontHote

        return AnnonceurPontHote(settings)
    return AnnonceurJournal()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    atelier_factory = build_atelier_factory(settings)
    llm = build_llm(settings)
    annonceur = build_annonceur(settings)
    boucle = BoucleCodeAct(moteur_llm=llm, budget_pas=settings.budget_pas)
    gestionnaire = GestionnaireTaches(
        atelier_factory=atelier_factory, boucle=boucle, annonceur=annonceur
    )
    mcp = build_mcp(gestionnaire)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if settings.atelier_backend == "docker":
            from app.atelier.docker import nettoyer_orphelins

            await nettoyer_orphelins()
        async with mcp.session_manager.run():
            yield

    app = FastAPI(title="Action Forge", lifespan=lifespan)
    app.state.settings = settings
    app.state.atelier_factory = atelier_factory
    app.state.gestionnaire = gestionnaire
    app.include_router(router)
    app.include_router(router_atelier)
    app.mount("/mcp", mcp.streamable_http_app())

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app
