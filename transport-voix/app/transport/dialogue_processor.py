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
- il relaie au client les **appels d'outils** du DF (`AppelOutilVu` du flux) via
  un `RTVIServerMessageFrame` : le DF remplace l'étage LLM, donc les événements
  `llm-function-call-*` RTVI natifs ne se déclenchent pas — l'indicateur
  d'outils du module A4 (ticket 0008) dépend de ce relais ;
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
from pipecat.processors.frameworks.rtvi.frames import RTVIServerMessageFrame
from pipecat.services.settings import TTSSettings

from app.dialogue.base import AppelOutilVu, ClientDialogue, FinTour, Phrase
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
            # Publie l'id au client (module A4) : la page tient sa propre
            # conversation « fantôme » utile en isolé, mais dès qu'elle connaît
            # l'id *live*, ses menus (voix, historique) le visent — sinon ils
            # commanderaient une conversation que le transport n'utilise pas
            # (ticket 0008). Server-message RTVI, comme pour les outils.
            await self.push_frame(
                RTVIServerMessageFrame(
                    data={
                        "kind": "conversation",
                        "id": self._conversation,
                        "persona": self._persona,
                    }
                )
            )

    def changer_persona(self, persona: str) -> None:
        """Change le persona pilote (commande de la page, ADR 0012 : changer =
        nouvelle conversation). Effet : la conversation courante est abandonnée ;
        le prochain tour en crée une neuve avec ce persona, dont l'id sera
        republié. La voix repart de la voix de montage (dérogation remise à zéro
        par la nouvelle conversation)."""
        self._persona = persona
        self._conversation = None

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
            elif isinstance(evenement, AppelOutilVu):
                # Signale l'appel d'outil au client (module A4) : le DF remplace
                # l'étage LLM, donc les `llm-function-call-*` RTVI natifs ne se
                # déclenchent pas — on émet un message serveur RTVI que le
                # RTVIObserver relaiera au canal de données (type `server-message`).
                await self.push_frame(
                    RTVIServerMessageFrame(
                        data={"kind": "outil-appele", "nom": evenement.nom}
                    )
                )
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
