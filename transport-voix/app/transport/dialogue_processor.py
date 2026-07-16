"""Processeur Pipecat qui insère le Dialogue Forge dans le pipeline voix.

⚠️ Jamais exécuté à ce jour — ne pas présenter comme fonctionnel. Ce module
importe Pipecat (présent seulement sous l'extra `pipecat`) : il n'est donc
importé qu'en différé, depuis `TransportPipecat.executer_session`.

Rôle : le pipeline Pipecat standard place un service LLM entre le STT et le
TTS. Ici le « cerveau » n'est pas un LLM OpenAI mais le **Dialogue Forge**
(REST/NDJSON, ADR 0009). Ce processeur remplace donc l'étage LLM :
- il reçoit la transcription finale de l'utilisateur (`TranscriptionFrame`) ;
- il joue un tour via le client Dialogue Forge et **pousse chaque phrase** en
  aval sous forme de `TextFrame`, que le TTS synthétise (le DF segmente déjà
  phrase par phrase, ADR 0010) ;
- il applique la **voix portée par le flux** (ADR 0012 décision 5) : chaque
  phrase du NDJSON porte sa voix courante ; quand elle change, le processeur
  émet un `TTSUpdateSettingsFrame` (mécanisme Pipecat officiel de changement de
  réglage TTS en cours de pipeline) **avant** le `TextFrame` concerné, si bien
  que le TTS synthétise ce tour avec la bonne voix ;
- sur interruption (`InterruptionFrame`), il signale au DF le préfixe
  réellement prononcé pour qu'il tronque son dernier tour (ADR 0012 décision 3).

⚠️ Détails à confirmer au **premier run réel** (le taxon de frames Pipecat n'a
jamais tourné ici) : le fait que pousser des `TextFrame` bruts alimente
correctement le TTS ; le suivi exact du « préfixe prononcé » (approximé ici par
les phrases déjà dépêchées — un suivi fin demanderait de compter les
`BotStoppedSpeaking`/`TTSStopped`).
"""

from pipecat.frames.frames import (
    Frame,
    InterruptionFrame,
    LLMFullResponseEndFrame,
    LLMFullResponseStartFrame,
    TextFrame,
    TranscriptionFrame,
    TTSUpdateSettingsFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.services.settings import TTSSettings

from app.dialogue.base import ClientDialogue, FinTour, Phrase
from app.transport.selecteur_voix import SelecteurVoix


class ProcesseurDialogueForge(FrameProcessor):
    """Pont Pipecat ↔ Dialogue Forge (remplace l'étage LLM du pipeline)."""

    def __init__(
        self,
        dialogue: ClientDialogue,
        *,
        persona: str | None = None,
        voix_defaut: str,
    ) -> None:
        super().__init__()
        self._dialogue = dialogue
        self._persona = persona
        self._conversation: str | None = None
        # Suit la voix appliquée au TTS pour n'émettre un TTSUpdateSettingsFrame
        # que lorsque le flux change de voix (départ = voix de montage du TTS).
        self._selecteur_voix = SelecteurVoix(voix_defaut)
        # Phrases dépêchées au TTS pour le tour en cours (base du préfixe
        # prononcé signalé au DF en cas d'interruption).
        self._phrases_en_cours: list[str] = []

    async def process_frame(self, frame: Frame, direction: FrameDirection) -> None:
        await super().process_frame(frame, direction)

        if isinstance(frame, InterruptionFrame):
            await self._signaler_interruption()
            await self.push_frame(frame, direction)
        elif isinstance(frame, TranscriptionFrame):
            # Ne pas propager la transcription telle quelle : on répond à la place.
            await self._jouer_tour(frame.text)
        else:
            await self.push_frame(frame, direction)

    async def _assurer_conversation(self) -> None:
        if self._conversation is None:
            self._conversation = await self._dialogue.creer_conversation(self._persona)

    async def _jouer_tour(self, texte_utilisateur: str) -> None:
        await self._assurer_conversation()
        assert self._conversation is not None
        self._phrases_en_cours = []
        await self.push_frame(LLMFullResponseStartFrame())
        async for evenement in self._dialogue.jouer_tour(self._conversation, texte_utilisateur):
            if isinstance(evenement, Phrase):
                # Applique la voix du flux avant la phrase : si elle diffère de
                # la voix courante du TTS, on la met à jour d'abord.
                voix = self._selecteur_voix.changement(evenement.voix)
                if voix is not None:
                    await self.push_frame(
                        TTSUpdateSettingsFrame(delta=TTSSettings(voice=voix))
                    )
                self._phrases_en_cours.append(evenement.texte)
                await self.push_frame(TextFrame(evenement.texte))
            elif isinstance(evenement, FinTour):
                break
        await self.push_frame(LLMFullResponseEndFrame())

    async def _signaler_interruption(self) -> None:
        if self._conversation is None or not self._phrases_en_cours:
            return
        # Best-effort : le préfixe réellement prononcé ≈ les phrases dépêchées.
        prefixe_prononce = " ".join(self._phrases_en_cours)
        await self._dialogue.interrompre(self._conversation, prefixe_prononce)
        self._phrases_en_cours = []
