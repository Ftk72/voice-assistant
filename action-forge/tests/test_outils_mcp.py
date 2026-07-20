import asyncio

import pytest

from app.annonce.journal import AnnonceurJournal
from app.atelier.fake import AtelierFactice
from app.boucle import BoucleCodeAct
from app.gestionnaire import GestionnaireTaches
from app.llm.base import MoteurLLM
from app.llm.factice import MoteurLLMFactice
from app.mcp_server import build_mcp


class _MoteurBloquant(MoteurLLM):
    """Ne répond jamais seul — pour tester qu'une Tâche confiée reste en cours."""

    async def completer(self, messages):
        await asyncio.Event().wait()


def _gestionnaire(reponses: list[str] | None = None, bloquant: bool = False):
    llm = _MoteurBloquant() if bloquant else MoteurLLMFactice(reponses=reponses or [])
    boucle = BoucleCodeAct(moteur_llm=llm, budget_pas=8)
    return GestionnaireTaches(
        atelier_factory=AtelierFactice, boucle=boucle, annonceur=AnnonceurJournal()
    )


@pytest.fixture
def gestionnaire():
    return _gestionnaire(bloquant=True)


@pytest.fixture
def mcp(gestionnaire):
    return build_mcp(gestionnaire)


async def call_tool(mcp, name: str, arguments: dict) -> str:
    result = await mcp.call_tool(name, arguments)
    content = result[0] if isinstance(result, tuple) else result
    return content[0].text


async def test_confier_tache_rend_la_main_sans_attendre(mcp, gestionnaire):
    reponse = await call_tool(mcp, "confier_tache", {"enonce": "fais un truc"})

    assert reponse == "Je m'y mets."
    assert len(gestionnaire.lister()) == 1
    assert gestionnaire.lister()[0].statut == "en_cours"


async def test_ou_en_est_la_tache_sans_argument_vise_la_derniere_en_cours(mcp, gestionnaire):
    await call_tool(mcp, "confier_tache", {"enonce": "premiere"})
    await asyncio.sleep(0)
    await call_tool(mcp, "confier_tache", {"enonce": "deuxieme"})
    await asyncio.sleep(0)

    reponse = await call_tool(mcp, "ou_en_est_la_tache", {})

    assert "en cours" in reponse


async def test_ou_en_est_la_tache_sans_tache_en_cours():
    gestionnaire = _gestionnaire(reponses=[])
    mcp = build_mcp(gestionnaire)

    reponse = await call_tool(mcp, "ou_en_est_la_tache", {})

    assert reponse == "Aucune tâche en cours."


async def test_annuler_tache_sans_argument_annule_la_derniere_en_cours(mcp, gestionnaire):
    await call_tool(mcp, "confier_tache", {"enonce": "fais un truc"})
    await asyncio.sleep(0)

    reponse = await call_tool(mcp, "annuler_tache", {})

    assert reponse == "Tâche annulée."
    assert gestionnaire.lister()[0].statut == "annulee"


async def test_annuler_tache_sans_tache_en_cours():
    gestionnaire = _gestionnaire(reponses=[])
    mcp = build_mcp(gestionnaire)

    reponse = await call_tool(mcp, "annuler_tache", {})

    assert reponse == "Aucune tâche en cours."
