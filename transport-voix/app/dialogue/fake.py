"""Adaptateur de dialogue factice, scriptable par les tests. Aucun réseau."""

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from uuid import uuid4

from app.dialogue.base import ClientDialogue, FinTour, Phrase


@dataclass
class ClientDialogueFactice(ClientDialogue):
    """Client en mémoire : `jouer_tour` émet quelques phrases scriptées (voix
    par défaut) puis un `FinTour` ; `interrompre` et `clore` journalisent
    leurs appels pour les assertions de tests."""

    voix_par_defaut: str = "Emma"
    phrases: list[str] = field(default_factory=lambda: ["Bonjour.", "Comment puis-je aider ?"])
    conversations: list[str] = field(default_factory=list)
    interruptions: list[tuple[str, str]] = field(default_factory=list)
    clotures: list[str] = field(default_factory=list)

    async def creer_conversation(self, persona: str | None = None) -> str:
        identifiant = str(uuid4())
        self.conversations.append(identifiant)
        return identifiant

    async def jouer_tour(self, conversation: str, texte: str) -> AsyncIterator[Phrase | FinTour]:
        for phrase in self.phrases:
            yield Phrase(texte=phrase, voix=self.voix_par_defaut)
        yield FinTour(reponse=" ".join(self.phrases))

    async def interrompre(self, conversation: str, prefixe_prononce: str) -> None:
        self.interruptions.append((conversation, prefixe_prononce))

    async def clore(self, conversation: str) -> bool:
        self.clotures.append(conversation)
        return True
