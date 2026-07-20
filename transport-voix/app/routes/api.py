from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response
from fastapi.responses import FileResponse, RedirectResponse

router = APIRouter()

# Client navigateur minimal de prototypage du pont WebView2↔Pipecat.
PROTOTYPE = Path(__file__).resolve().parent.parent / "web" / "prototype.html"


@router.get("/", include_in_schema=False)
def racine() -> RedirectResponse:
    """Confort de dev : la racine mène au client de prototypage."""
    return RedirectResponse(url="/prototype")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/offer")
async def offer(corps: dict, background_tasks: BackgroundTasks, request: Request) -> dict:
    """Signaling WebRTC (SmallWebRTC, ADR 0012) : reçoit l'offre SDP de la
    webview, crée (ou renégocie) une connexion pair-à-pair et renvoie la
    réponse SDP. La session Pipecat (STT → Dialogue Forge → TTS) tourne en
    tâche de fond pour la durée de la connexion.

    Actif uniquement quand le transport Pipecat est sélectionné
    (`TRANSPORT_VOIX_TRANSPORT_BACKEND=pipecat`) ; sinon **503** : le chemin
    factice n'établit aucune session temps réel. ⚠️ Jamais exécuté à ce jour —
    dépend de l'extra `pipecat` (non installé par défaut)."""
    settings = request.app.state.settings
    if settings.transport_backend != "pipecat":
        raise HTTPException(
            status_code=503,
            detail="Transport Pipecat non activé (TRANSPORT_VOIX_TRANSPORT_BACKEND=pipecat).",
        )

    # Imports différés : Pipecat n'est présent que sous l'extra `pipecat`.
    from pipecat.transports.smallwebrtc.connection import IceServer, SmallWebRTCConnection

    connexions: dict[str, object] = request.app.state.webrtc_connexions
    transport = request.app.state.transport
    ice = [IceServer(urls=url) for url in settings.stun_urls]
    if settings.turn_url:
        # coturn local : donne à Pipecat un candidat « relay » sur le même relais
        # que le navigateur, d'où passe toute la media (cf. docs/impasses.md).
        ice.append(
            IceServer(
                urls=settings.turn_url,
                username=settings.turn_user,
                credential=settings.turn_password,
            )
        )

    pc_id = corps.get("pc_id")
    if pc_id and pc_id in connexions:
        connexion = connexions[pc_id]
        await connexion.renegotiate(
            sdp=corps["sdp"], type=corps["type"], restart_pc=corps.get("restart_pc", False)
        )
    else:
        connexion = SmallWebRTCConnection(ice)
        await connexion.initialize(sdp=corps["sdp"], type=corps["type"])

        @connexion.event_handler("closed")
        async def _fermee(c: SmallWebRTCConnection) -> None:
            connexions.pop(c.pc_id, None)

        background_tasks.add_task(transport.executer_session, connexion)

    reponse = connexion.get_answer()
    connexions[reponse["pc_id"]] = connexion
    return reponse


@router.get("/conversation")
def conversation(request: Request) -> dict[str, bool]:
    """État de la session temps réel, tel que le Pont hôte l'interroge avant de
    jouer une annonce (ticket wayfinder 0044). Conversation ouverte = micro vif :
    l'annonce doit passer par le flux sortant, pas par les enceintes."""
    return {"ouverte": request.app.state.transport.conversation_ouverte()}


@router.post("/annonce", status_code=202)
async def annonce(request: Request) -> Response:
    """Reçoit un WAV d'annonce (corps brut) et l'injecte dans le flux WebRTC
    sortant de la conversation en cours, où l'annulation d'écho de la coquille
    peut le voir — et donc le soustraire du micro, au lieu de laisser l'assistant
    se répondre à lui-même (ticket wayfinder 0044).

    **202** si l'annonce est partie dans la conversation ; **409** si aucune
    session ne peut la jouer — le Pont hôte se rabat alors sur les enceintes."""
    wav = await request.body()
    if not await request.app.state.transport.jouer_annonce(wav):
        raise HTTPException(
            status_code=409,
            detail="Aucune conversation ouverte : l'annonce ne peut pas être injectée.",
        )
    return Response(status_code=202)


@router.get("/prototype", include_in_schema=False)
def prototype() -> FileResponse:
    """Client navigateur minimal (getUserMedia + WebRTC) pour valider le pont
    WebView2↔Pipecat « un seul inconnu à la fois » (ADR 0012 décision 2, bouton
    d'abord). Outil de développement — **pas** le module dialogue (front A4,
    servi par le Dialogue Forge)."""
    return FileResponse(PROTOTYPE)
