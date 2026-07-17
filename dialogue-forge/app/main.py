import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import Settings
from app.dialogue import Orchestrateur
from app.llm.base import MoteurLLM
from app.llm.fake import MoteurLLMFactice
from app.memoire.base import MoteurMemoire
from app.memoire.fake import MemoireFactice
from app.outils.base import MoteurOutils
from app.outils.fake import OutilsFactices
from app.personas import charger_personas
from app.routes.api import router
from app.routes.module_dialogue import router as router_module_dialogue

logger = logging.getLogger(__name__)


def build_llm(settings: Settings) -> MoteurLLM:
    if settings.llm_backend == "openai":
        from app.llm.openai_compat import MoteurLLMOpenAI

        return MoteurLLMOpenAI(settings)
    return MoteurLLMFactice()


def build_memoire(settings: Settings) -> MoteurMemoire:
    if settings.memoire_backend == "rest":
        from app.memoire.rest import MemoireREST

        return MemoireREST(settings)
    return MemoireFactice()


def build_outils(settings: Settings) -> MoteurOutils:
    if settings.outils_backend == "mcp":
        from app.outils.mcp import OutilsMCP

        return OutilsMCP(settings.mcp_urls)
    return OutilsFactices()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    llm = build_llm(settings)
    memoire = build_memoire(settings)
    outils = build_outils(settings)
    personas = charger_personas(settings.personas_dir)
    orchestrateur = Orchestrateur(llm, memoire, outils, settings.max_iterations_outils)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Outils listés une seule fois au démarrage : le préfixe du prompt
        # envoyé au LLM reste stable d'un tour à l'autre (cache de contexte).
        orchestrateur.definir_outils(await outils.lister_outils())
        logger.info("Dialogue Forge démarré (%d persona(s) chargé(s))", len(personas))
        yield
        # Ferme proprement les clients HTTP des adaptateurs réels, s'il y en a.
        for composant in (llm, memoire):
            fermer = getattr(composant, "aclose", None)
            if fermer is not None:
                await fermer()

    app = FastAPI(title="Dialogue Forge", lifespan=lifespan)
    app.state.settings = settings
    app.state.llm = llm
    app.state.memoire = memoire
    app.state.outils = outils
    app.state.personas = personas
    app.state.orchestrateur = orchestrateur
    app.state.conversations = {}
    app.include_router(router)
    app.include_router(router_module_dialogue)
    return app
