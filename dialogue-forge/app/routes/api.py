import json
import logging
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, Response
from fastapi.responses import StreamingResponse

from app.schemas import (
    ConversationVue,
    CreerConversation,
    DerogationVoix,
    Interruption,
    PersonaRef,
    TourIn,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/personas", response_model=list[PersonaRef])
def lister_personas(request: Request) -> list[PersonaRef]:
    personas = request.app.state.personas
    return [PersonaRef(nom=p.nom, voix=p.voix) for p in personas.values()]


@router.get("/voix")
async def lister_voix(request: Request) -> dict[str, list[dict]]:
    """Toutes les voix enrôlées (réglage grand public, ticket 0014). En cas de
    panne du catalogue (voice-forge injoignable), replie sur les voix des
    personas : le menu n'est jamais vide."""
    catalogue = request.app.state.catalogue_voix
    try:
        return {"voix": await catalogue.lister()}
    except Exception:
        logger.warning(
            "Catalogue de voix indisponible : repli sur les voix des personas", exc_info=True
        )
        personas = request.app.state.personas
        vues = {p.voix for p in personas.values()}
        return {"voix": [{"id": v, "nom": v} for v in sorted(vues)]}


@router.post("/voix/{voix_id}/apercu")
async def apercevoir_voix(voix_id: str, request: Request) -> Response:
    catalogue = request.app.state.catalogue_voix
    try:
        contenu = await catalogue.apercu(voix_id)
    except Exception as erreur:
        raise HTTPException(status_code=502, detail="Aperçu de voix indisponible") from erreur
    return Response(content=contenu, media_type="audio/wav")


@router.post("/conversations", status_code=201)
def creer_conversation(corps: CreerConversation, request: Request) -> dict[str, str]:
    personas = request.app.state.personas
    prefs = request.app.state.preferences
    cle = (corps.persona or prefs.persona).lower()
    if cle not in personas:
        raise HTTPException(status_code=404, detail=f"Persona inconnu : {corps.persona}")
    identifiant = uuid4().hex
    request.app.state.conversations[identifiant] = {
        "persona": personas[cle].nom,
        "cle_persona": cle,
        "historique": [],
        # Aucune dérogation au départ, sauf préférence enregistrée adoptée
        # quand aucun persona explicite n'a été demandé (ticket 0014).
        "voix_derogee": prefs.voix if corps.persona is None and prefs.voix else None,
    }
    return {"id": identifiant}


@router.get("/conversations/{identifiant}", response_model=ConversationVue)
def lire_conversation(identifiant: str, request: Request) -> ConversationVue:
    conversation = request.app.state.conversations.get(identifiant)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation inconnue")
    return ConversationVue(
        id=identifiant,
        persona=conversation["persona"],
        historique=conversation["historique"],
    )


@router.post("/conversations/{identifiant}/tours")
async def jouer_tour(identifiant: str, corps: TourIn, request: Request) -> StreamingResponse:
    conversation = request.app.state.conversations.get(identifiant)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation inconnue")

    orchestrateur = request.app.state.orchestrateur
    persona = request.app.state.personas[conversation["cle_persona"]]

    async def flux():
        async for evenement in orchestrateur.jouer_tour(
            persona,
            conversation["historique"],
            corps.texte,
            voix=conversation.get("voix_derogee"),
        ):
            yield json.dumps(evenement, ensure_ascii=False) + "\n"

    return StreamingResponse(flux(), media_type="application/x-ndjson")


@router.post("/conversations/{identifiant}/voix")
def deroger_voix(
    identifiant: str, corps: DerogationVoix, request: Request
) -> dict[str, str]:
    """Déroge la voix du persona pour la conversation en cours (ADR 0012
    décision 5) : effet au **tour suivant** (le tour en cours de synthèse garde
    sa voix). La coquille pilote ce menu ; le persona, lui, reste inchangé."""
    conversation = request.app.state.conversations.get(identifiant)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation inconnue")
    conversation["voix_derogee"] = corps.voix
    return {"voix": corps.voix}


@router.post("/conversations/{identifiant}/interrompre")
def interrompre_conversation(
    identifiant: str, corps: Interruption, request: Request
) -> dict[str, bool]:
    """Interruption (ADR 0012 décision 3) : le transport voix signale le préfixe
    réellement prononcé ; on tronque le dernier tour assistant à ce préfixe. Sert
    la cohérence *live* — la mémoire, elle, est immunisée (user-only, ADR 0011)."""
    conversation = request.app.state.conversations.get(identifiant)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation inconnue")
    tronque = request.app.state.orchestrateur.interrompre(
        conversation["historique"], corps.prefixe
    )
    return {"tronque": tronque}


@router.post("/conversations/{identifiant}/clore")
async def clore_conversation(identifiant: str, request: Request) -> dict[str, bool]:
    """Ferme la conversation : capture l'épisode (tours utilisateur uniquement,
    ADR 0011) puis retire la conversation de l'état. En attendant qu'A2 (transport
    voix) appelle cette route à la mise en veille, c'est le déclencheur explicite."""
    conversation = request.app.state.conversations.get(identifiant)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation inconnue")

    orchestrateur = request.app.state.orchestrateur
    persona = request.app.state.personas[conversation["cle_persona"]]
    capture = await orchestrateur.clore_conversation(
        conversation["historique"], nom=identifiant, off_record=persona.off_record
    )
    del request.app.state.conversations[identifiant]
    return {"episode_capture": capture}
