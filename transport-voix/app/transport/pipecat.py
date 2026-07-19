"""Adaptateur transport réel (Pipecat / SmallWebRTC).

⚠️ Exécution end-to-end jamais lancée — ne pas présenter comme fonctionnel. Le
pont WebRTC WebView2↔Pipecat n'a **jamais été prototypé** (ADR 0012, risque n°1).

Ce qui **est** vérifié (contre Pipecat 1.5.0 réellement installé) : tous les
imports résolvent, les constructeurs acceptent nos arguments, et le pipeline se
**construit** sans avertissement (cf. la session de vérification). Ce qui
**reste** à valider au premier run réel sur la machine de l'utilisateur : le
comportement à l'exécution (aller-retour audio WebRTC, gating VAD, STT/DF/TTS
live, précision du préfixe d'interruption) — il faut navigateur + micro +
services STT/TTS/DF en marche.

Tous les imports Pipecat sont **différés** dans les méthodes : Pipecat n'est
présent que sous l'extra `pipecat` (`uv sync --extra pipecat`), et le reste du
composant (chemin factice, tests) doit fonctionner sans lui.

Choix d'architecture : dans ce chemin réel, le STT et le TTS sont les services
**natifs Pipecat** OpenAI-compat (branchés respectivement sur whisper.cpp et
voice-forge, tous deux OpenAI-compat) ; seul le « cerveau » — le Dialogue
Forge — n'a pas d'équivalent natif et passe par notre port `ClientDialogue`
(adaptateur REST) enveloppé dans `ProcesseurDialogueForge`.
"""

import logging
import wave
from pathlib import Path

from app.config import Settings
from app.transport.base import Transport

logger = logging.getLogger(__name__)


def _charger_wav_pcm16(chemin: Path) -> tuple[bytes, int, int]:
    """Lit un WAV PCM16 (module standard, aucune dépendance de décodage) et
    renvoie (échantillons, fréquence, canaux) — ce que veut `OutputAudioRawFrame`.

    Le fichier attendu est déjà au format cible (PCM16, cf. `assets/README.md`) :
    aucune conversion ici, c'est fait une fois pour toutes en amont (ffmpeg)."""
    with wave.open(str(chemin), "rb") as f:
        if f.getsampwidth() != 2:
            raise ValueError(f"{chemin} n'est pas en PCM 16 bits (sampwidth={f.getsampwidth()})")
        return f.readframes(f.getnframes()), f.getframerate(), f.getnchannels()


class TransportPipecat(Transport):
    """Fabrique et exécute une session Pipecat par connexion WebRTC.

    SmallWebRTC est **par connexion** : il n'y a pas de session persistante à
    « démarrer » globalement. `demarrer`/`arreter` (contrat du port) sont donc
    des points d'entrée neutres ; le vrai travail est `executer_session`,
    appelé par la route de signaling `/offer` pour chaque connexion entrante.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def demarrer(self) -> None:
        """SmallWebRTC n'a pas de session globale : rien à établir ici (les
        sessions naissent par connexion, via `executer_session`)."""

    async def arreter(self) -> None:
        """Idem : la fermeture est gérée par connexion (handler `closed`)."""

    async def executer_session(self, connexion: object) -> None:
        """Construit et fait tourner le pipeline voix pour une connexion WebRTC
        déjà négociée (`SmallWebRTCConnection`). Bloque jusqu'à la fin de la
        session. ⚠️ Jamais exécuté à ce jour."""
        # --- Imports différés (extra `pipecat` uniquement) ---
        from pipecat.audio.vad.silero import SileroVADAnalyzer
        from pipecat.frames.frames import OutputAudioRawFrame
        from pipecat.pipeline.pipeline import Pipeline
        from pipecat.pipeline.worker import PipelineParams, PipelineWorker
        from pipecat.processors.audio.vad_processor import VADProcessor
        from pipecat.processors.frameworks.rtvi import RTVIProcessor
        from pipecat.services.openai.stt import OpenAISTTService
        from pipecat.transcriptions.language import Language
        from pipecat.transports.base_transport import TransportParams
        from pipecat.transports.smallwebrtc.transport import SmallWebRTCTransport
        from pipecat.workers.runner import WorkerRunner

        from app.dialogue.rest import ClientDialogueREST
        from app.transport.dialogue_processor import ProcesseurDialogueForge
        from app.transport.tts_voiceforge import ServiceTTSVoiceForge

        s = self._settings

        # Accueil pré-enregistré (WAV statique, pas de synthèse) : lu une fois
        # par connexion, coût négligeable (~100 Ko).
        accueil_audio, accueil_taux, accueil_canaux = _charger_wav_pcm16(s.accueil_audio_path)

        transport = SmallWebRTCTransport(
            webrtc_connection=connexion,
            params=TransportParams(
                audio_in_enabled=True,
                audio_out_enabled=True,
            ),
        )

        # Pipecat 1.5 : le VAD est un processeur de pipeline explicite. Le
        # passer en `vad_analyzer=` à TransportParams (API pré-1.5) est ignoré
        # en silence par pydantic — Silero se charge mais n'analyse jamais rien
        # (payé au premier run réel : parole jamais détectée, cf.
        # docs/impasses.md 2026-07-16). Le VADProcessor émet les trames
        # VADUserStarted/StoppedSpeakingFrame qu'attend le STT segmenté.
        vad = VADProcessor(vad_analyzer=SileroVADAnalyzer())

        # STT whisper.cpp et TTS voice-forge, via l'API OpenAI-compat de chacun.
        # Réglages via `.Settings(...)` (les kwargs `model`/`voice` directs sont
        # dépréciés en Pipecat 1.5).
        # `language` explicite : sans lui, OpenAISTTService retombe sur l'anglais
        # (Language.EN) et annoncerait à Voxtral un audio anglais — or tout est en
        # français (s.langue). Language('fr') = Language.FR.
        stt = OpenAISTTService(
            api_key=s.stt_api_key,
            base_url=s.stt_base_url,
            settings=OpenAISTTService.Settings(
                model=s.stt_model, language=Language(s.langue)
            ),
        )
        # voice-forge n'est pas un client OpenAI neutre : voix hors énum OpenAI et
        # sortie WAV (pas PCM). Notre sous-classe lève ces deux blocages.
        tts = ServiceTTSVoiceForge(
            api_key=s.tts_api_key,
            base_url=s.tts_base_url,
            settings=ServiceTTSVoiceForge.Settings(voice=s.tts_voix_defaut, model=s.tts_model),
        )

        dialogue = ClientDialogueREST(s.dialogue_base_url)
        # `voix_defaut` = voix de montage du TTS (ci-dessus) : le processeur ne
        # signalera un changement de voix que si le flux Dialogue Forge en porte
        # une différente (dérogation effective au tour suivant, ADR 0012 déc. 5).
        processeur_df = ProcesseurDialogueForge(
            dialogue, persona=s.persona_defaut, voix_defaut=s.tts_voix_defaut
        )

        pipeline = Pipeline(
            [
                transport.input(),  # audio micro depuis la webview
                vad,  # détection de parole (Silero) — segmente pour le STT
                stt,  # whisper.cpp (batch)
                processeur_df,  # Dialogue Forge (remplace l'étage LLM)
                tts,  # voice-forge
                transport.output(),  # audio synthétisé vers la webview
            ]
        )

        # RTVIProcessor explicite : on a besoin d'une référence pour recevoir les
        # **commandes de la page** (module A4 — changer de persona). Le passer à
        # PipelineWorker via `rtvi_processor=` est la voie sanctionnée : le worker
        # le prépend lui-même au pipeline et crée l'observer (pas de recâblage
        # manuel, pas de doublon). Le client envoie un `client-message`
        # `{t:"persona", d:{nom}}` ; le handler recrée la conversation (le nouvel
        # id est republié par le processeur, la page l'adopte).
        rtvi = RTVIProcessor()

        @rtvi.event_handler("on_client_message")
        async def _sur_commande(_rtvi: object, frame: object) -> None:
            # frame : RTVIClientMessageFrame(type=<t>, data=<d>).
            if frame.type == "persona" and frame.data:
                processeur_df.changer_persona(frame.data["nom"])

        worker = PipelineWorker(
            pipeline, params=PipelineParams(enable_metrics=True), rtvi_processor=rtvi
        )

        @transport.event_handler("on_client_connected")
        async def _connecte(_transport: object, _client: object) -> None:
            # Accueil à la connexion : WAV pré-enregistré joué tel quel (frame
            # audio brute, pas de TTS) — bisecte la voie **sortante**
            # (WebRTC) indépendamment du micro/STT — si on l'entend, seule
            # l'entrée reste à corriger.
            await worker.queue_frames(
                [
                    OutputAudioRawFrame(
                        audio=accueil_audio,
                        sample_rate=accueil_taux,
                        num_channels=accueil_canaux,
                    )
                ]
            )

        @transport.event_handler("on_client_disconnected")
        async def _deconnecte(_transport: object, _client: object) -> None:
            await worker.cancel()

        runner = WorkerRunner(handle_sigint=False)
        try:
            await runner.add_workers(worker)
            await runner.run()
        finally:
            await dialogue.aclose()
