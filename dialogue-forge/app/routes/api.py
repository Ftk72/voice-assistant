import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.schemas import ConversationVue, CreerConversation, PersonaRef, TourIn

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/personas", response_model=list[PersonaRef])
def lister_personas(request: Request) -> list[PersonaRef]:
    personas = request.app.state.personas
    return [PersonaRef(nom=p.nom, voix=p.voix) for p in personas.values()]


@router.post("/conversations", status_code=201)
def creer_conversation(corps: CreerConversation, request: Request) -> dict[str, str]:
    personas = request.app.state.personas
    cle = (corps.persona or request.app.state.settings.persona_defaut).lower()
    if cle not in personas:
        raise HTTPException(status_code=404, detail=f"Persona inconnu : {corps.persona}")
    identifiant = uuid4().hex
    request.app.state.conversations[identifiant] = {
        "persona": personas[cle].nom,
        "cle_persona": cle,
        "historique": [],
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
            persona, conversation["historique"], corps.texte
        ):
            yield json.dumps(evenement, ensure_ascii=False) + "\n"

    return StreamingResponse(flux(), media_type="application/x-ndjson")


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
