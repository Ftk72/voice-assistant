"""Ticket 0043 : le Dialogue Forge survit à une forge d'outils absente.

Couvre la tolérance à l'échec de `OutilsMCP.lister_outils`, la reprise à
palier de `rafraichir`, le point d'audit `/health` + `etat_forges`, et
l'adoption du catalogue rafraîchi par l'orchestrateur. `_lister_une` est
monkeypatché plutôt que la pile MCP entière : aucun test n'ouvre de socket.
"""

import logging

import pytest
from fastapi.testclient import TestClient

from app.dialogue import Orchestrateur
from app.llm.base import DefinitionOutil
from app.llm.fake import MoteurLLMFactice, TourTexte
from app.main import create_app
from app.memoire.fake import MemoireFactice
from app.outils.fake import OutilsFactices
from app.outils.mcp import OutilsMCP, _EtatUrl
from app.personas import Persona

URLS = ["http://time/mcp", "http://world/mcp", "http://memory/mcp", "http://action/mcp"]


def _definition(nom: str) -> DefinitionOutil:
    return {
        "type": "function",
        "function": {"name": nom, "description": "", "parameters": {}},
    }


class _HorlogeFactice:
    """Horloge de test : le temps n'avance que quand on le décide."""

    def __init__(self, depart: float = 0.0) -> None:
        self.maintenant = depart

    def __call__(self) -> float:
        return self.maintenant

    def avancer(self, secondes: float) -> None:
        self.maintenant += secondes


def _brancher(moteur: OutilsMCP, reponses: dict[str, list[DefinitionOutil] | Exception]):
    """Monkeypatch `_lister_une` : `reponses[url]` est soit une liste de
    définitions (succès), soit une exception à lever (échec)."""

    async def _lister_une(url: str) -> list[DefinitionOutil]:
        valeur = reponses[url]
        if isinstance(valeur, Exception):
            raise valeur
        return valeur

    moteur._lister_une = _lister_une  # type: ignore[method-assign]


# --- lister_outils : tolérance --------------------------------------------


async def test_une_seule_forge_en_echec_laisse_le_catalogue_des_survivantes(caplog):
    moteur = OutilsMCP(URLS[:2])
    _brancher(
        moteur,
        {
            URLS[0]: [_definition("heure")],
            URLS[1]: RuntimeError("connexion refusée"),
        },
    )
    with caplog.at_level(logging.WARNING):
        catalogue = await moteur.lister_outils()

    assert [d["function"]["name"] for d in catalogue] == ["heure"]
    assert any("injoignable" in enreg.message for enreg in caplog.records)


async def test_les_quatre_forges_en_echec_donnent_un_catalogue_vide_sans_lever():
    moteur = OutilsMCP(URLS)
    _brancher(moteur, {url: RuntimeError("injoignable") for url in URLS})

    catalogue = await moteur.lister_outils()

    assert catalogue == []


# --- rafraichir -------------------------------------------------------------


async def test_rafraichir_renvoie_none_quand_tout_va_bien():
    horloge = _HorlogeFactice()
    moteur = OutilsMCP(URLS[:1], palier_reprise_s=60.0, horloge=horloge)
    _brancher(moteur, {URLS[0]: [_definition("heure")]})
    await moteur.lister_outils()

    # On retire le branchement : si `rafraichir` ouvrait la moindre session,
    # l'attribut absent ferait planter le test (KeyError sur `reponses`).
    del moteur._lister_une

    assert await moteur.rafraichir() is None


async def test_rafraichir_attend_le_palier_puis_reprend_dans_l_ordre_des_urls():
    horloge = _HorlogeFactice()
    moteur = OutilsMCP(URLS[:2], palier_reprise_s=60.0, horloge=horloge)
    _brancher(
        moteur,
        {
            URLS[0]: [_definition("heure")],
            URLS[1]: RuntimeError("connexion refusée"),
        },
    )
    await moteur.lister_outils()

    # Palier pas écoulé : rien ne bouge.
    horloge.avancer(30)
    assert await moteur.rafraichir() is None

    # La forge revient, mais le palier reste insuffisant.
    _brancher(moteur, {URLS[0]: [_definition("heure")], URLS[1]: [_definition("meteo")]})
    horloge.avancer(29)  # total 59s < 60s
    assert await moteur.rafraichir() is None

    # Palier écoulé : reprise, catalogue complet dans l'ordre de self._urls.
    horloge.avancer(2)  # total 61s
    catalogue = await moteur.rafraichir()
    assert [d["function"]["name"] for d in catalogue] == ["heure", "meteo"]


async def test_apres_reprise_appeler_route_vers_la_forge_revenue():
    horloge = _HorlogeFactice()
    moteur = OutilsMCP(URLS[:1], palier_reprise_s=10.0, horloge=horloge)
    _brancher(moteur, {URLS[0]: RuntimeError("panne")})
    await moteur.lister_outils()

    _brancher(moteur, {URLS[0]: [_definition("meteo")]})
    horloge.avancer(11)
    await moteur.rafraichir()

    # `appeler` ouvre une vraie session MCP ; on ne teste ici que le routage,
    # en interceptant juste avant l'ouverture réseau.
    assert moteur._routage["meteo"] == URLS[0]


async def test_etat_forges_reflete_l_echec_puis_le_retour():
    horloge = _HorlogeFactice()
    moteur = OutilsMCP(URLS[:2], palier_reprise_s=10.0, horloge=horloge)
    _brancher(
        moteur,
        {URLS[0]: [_definition("heure")], URLS[1]: RuntimeError("panne réseau")},
    )
    await moteur.lister_outils()

    etats = moteur.etat_forges()
    assert etats[0] == {"url": URLS[0], "etat": "ok", "outils": 1, "erreur": None}
    assert etats[1]["etat"] == "injoignable"
    assert etats[1]["erreur"] == "panne réseau"

    _brancher(moteur, {URLS[0]: [_definition("heure")], URLS[1]: [_definition("meteo")]})
    horloge.avancer(11)
    await moteur.rafraichir()

    etats = moteur.etat_forges()
    assert etats[1] == {"url": URLS[1], "etat": "ok", "outils": 1, "erreur": None}


# --- /health -----------------------------------------------------------------


def test_health_porte_forges_outils_si_le_moteur_l_expose(settings):
    app = create_app(settings)
    app.state.outils = OutilsMCP(URLS[:1])
    app.state.outils._etats["http://time/mcp"] = _EtatUrl(definitions=[_definition("heure")])
    with TestClient(app) as client:
        reponse = client.get("/health")
    assert reponse.status_code == 200
    corps = reponse.json()
    assert "forges_outils" in corps
    assert corps["forges_outils"][0]["etat"] == "ok"


def test_health_avec_le_factice_reste_exactement_status_ok(client):
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json() == {"status": "ok"}


# --- Orchestrateur : adoption du catalogue rafraîchi --------------------------


@pytest.fixture
def persona() -> Persona:
    return Persona(nom="Assistant", voix="Emma", prompt="Sois bref.", off_record=False)


async def test_l_orchestrateur_adopte_le_catalogue_rafraichi_au_tour_suivant(persona):
    llm = MoteurLLMFactice(tours=[TourTexte("Bonjour."), TourTexte("Encore.")])
    outils = OutilsFactices(
        definitions=[_definition("ancien")],
        rafraichissements=[[_definition("ancien"), _definition("nouveau")]],
    )
    orchestrateur = Orchestrateur(llm, MemoireFactice(), outils)
    orchestrateur.definir_outils([_definition("ancien")])
    historique: list = []

    async for _ in orchestrateur.jouer_tour(persona, historique, "Salut"):
        pass

    assert [d["function"]["name"] for d in orchestrateur._outils_definitions] == [
        "ancien",
        "nouveau",
    ]
    assert outils.appels_rafraichir == 1


async def test_l_orchestrateur_ne_change_rien_quand_rafraichir_renvoie_none(persona):
    llm = MoteurLLMFactice(tours=[TourTexte("Bonjour.")])
    outils = OutilsFactices(definitions=[_definition("ancien")])  # rafraichissements vide
    orchestrateur = Orchestrateur(llm, MemoireFactice(), outils)
    orchestrateur.definir_outils([_definition("ancien")])
    historique: list = []

    async for _ in orchestrateur.jouer_tour(persona, historique, "Salut"):
        pass

    assert [d["function"]["name"] for d in orchestrateur._outils_definitions] == ["ancien"]
    assert outils.appels_rafraichir == 1


# --- Non-régression du bug d'origine ------------------------------------------


def test_create_app_demarre_avec_un_backend_mcp_partiellement_en_echec(settings, monkeypatch):
    """Reproduit le bug d'origine du ticket 0043 : avant le correctif,
    `orchestrateur.definir_outils(await outils.lister_outils())` dans le
    lifespan de `app/main.py` laissait remonter l'exception de la forge morte
    et FastAPI loguait `Application startup failed` (boucle de redémarrage
    sous `restart: unless-stopped`). On construit ici une app avec le vrai
    backend `mcp` et deux URLs, dont une qui lève systématiquement — le
    lifespan (donc `create_app` + `TestClient`) doit démarrer quand même."""
    settings = settings.model_copy(
        update={"outils_backend": "mcp", "mcp_urls": URLS[:2]}
    )

    reponses = {
        URLS[0]: [_definition("heure")],
        URLS[1]: RuntimeError("action-forge sur image périmée, sans route /mcp"),
    }

    async def _lister_une_patchee(self, url: str):
        valeur = reponses[url]
        if isinstance(valeur, Exception):
            raise valeur
        return valeur

    monkeypatch.setattr(OutilsMCP, "_lister_une", _lister_une_patchee)

    app = create_app(settings)
    with TestClient(app) as client:
        reponse = client.get("/health")

    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["forges_outils"][0]["etat"] == "ok"
    assert corps["forges_outils"][1]["etat"] == "injoignable"
    # Le catalogue de l'orchestrateur ne porte que les outils survivants.
    assert [d["function"]["name"] for d in app.state.orchestrateur._outils_definitions] == [
        "heure"
    ]
