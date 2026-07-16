"""Application de la voix du flux par le processeur Dialogue Forge.

Test d'intégration du câblage Pipecat : il ne s'exécute que si l'extra
`pipecat` est installé (sinon sauté — le reste du composant reste vert sans
lui). Il prouve que la voix portée par chaque phrase du flux se traduit bien
en `TTSUpdateSettingsFrame` poussé **avant** le `TextFrame` correspondant. La
logique de décision « quand changer » est, elle, couverte sans Pipecat par
`test_selecteur_voix.py`.
"""

from collections.abc import AsyncIterator

import pytest

pytest.importorskip("pipecat")

from pipecat.frames.frames import TextFrame, TTSUpdateSettingsFrame  # noqa: E402
from pipecat.processors.frame_processor import FrameDirection  # noqa: E402

from app.dialogue.base import ClientDialogue, FinTour, Phrase  # noqa: E402
from app.transport.dialogue_processor import ProcesseurDialogueForge  # noqa: E402


class _DialogueScripte(ClientDialogue):
    """Client factice qui rejoue des tours scriptés (texte, voix) par tour."""

    def __init__(self, tours: list[list[tuple[str, str]]]) -> None:
        self._tours = tours
        self._i = 0

    async def creer_conversation(self, persona: str | None = None) -> str:
        return "conv-1"

    async def jouer_tour(self, conversation: str, texte: str) -> AsyncIterator[Phrase | FinTour]:
        tour = self._tours[self._i]
        self._i += 1
        for texte_phrase, voix in tour:
            yield Phrase(texte=texte_phrase, voix=voix)
        yield FinTour(reponse=" ".join(t for t, _ in tour))

    async def interrompre(self, conversation: str, prefixe_prononce: str) -> None:
        return None

    async def clore(self, conversation: str) -> bool:
        return True


def _processeur_capturant(dialogue: ClientDialogue) -> tuple[ProcesseurDialogueForge, list]:
    """Monte un processeur dont `push_frame` capture les frames au lieu de les
    pousser dans un pipeline (non monté ici)."""
    processeur = ProcesseurDialogueForge(dialogue, voix_defaut="VoixDefaut")
    frames: list = []

    async def _capture(frame: object, direction: object = FrameDirection.DOWNSTREAM) -> None:
        frames.append(frame)

    processeur.push_frame = _capture  # type: ignore[method-assign]
    return processeur, frames


async def test_deux_tours_portant_deux_voix_le_tts_recoit_chacune():
    dialogue = _DialogueScripte(
        [
            [("Bonjour.", "Alice"), ("Comment ça va ?", "Alice")],
            [("Autre chose ?", "Bob")],
        ]
    )
    processeur, frames = _processeur_capturant(dialogue)

    await processeur._jouer_tour("salut")
    await processeur._jouer_tour("encore")

    updates = [f for f in frames if isinstance(f, TTSUpdateSettingsFrame)]
    # Un changement par tour (voix répétée dans le tour 1 → un seul update).
    assert [f.delta.voice for f in updates] == ["Alice", "Bob"]
    # Et le changement de voix précède bien le texte qu'il gouverne.
    i_update_alice = frames.index(updates[0])
    i_texte_alice = next(
        i for i, f in enumerate(frames) if isinstance(f, TextFrame) and f.text == "Bonjour."
    )
    assert i_update_alice < i_texte_alice


async def test_phrase_sans_voix_conserve_la_voix_par_defaut():
    dialogue = _DialogueScripte([[("Bonjour.", "")]])
    processeur, frames = _processeur_capturant(dialogue)

    await processeur._jouer_tour("salut")

    assert not any(isinstance(f, TTSUpdateSettingsFrame) for f in frames)
