"""Port du client de dialogue : le transport voix est *client* du Dialogue
Forge (l'orchestrateur/cerveau, ADR 0009), pas l'inverse."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class Phrase:
    """Une phrase de la réponse, prête à synthétiser. Porte la **voix
    courante** (elle peut changer d'une phrase à l'autre au sein d'un même
    tour — ADR 0012 décision 5)."""

    texte: str
    voix: str


@dataclass
class AppelOutilVu:
    """Un appel d'outil déclenché par le Dialogue Forge pendant le tour, à
    signaler à l'interface (indicateur d'outils appelés, module A4 / ticket
    0008). Le DF remplace l'étage LLM du pipeline : ses appels d'outils
    n'apparaissent donc pas dans les événements RTVI natifs — c'est son flux
    NDJSON qui les porte, et le transport les relaie au client."""

    nom: str


@dataclass
class FinTour:
    """Marque la fin d'un tour de dialogue, avec la réponse complète."""

    reponse: str


class ClientDialogue(ABC):
    """Port du client du Dialogue Forge : crée des conversations, y joue des
    tours (en streamant les phrases à synthétiser), signale les interruptions
    et clôt les conversations (déclenchant la capture mémoire, ADR 0011)."""

    @abstractmethod
    async def creer_conversation(self, persona: str | None = None) -> str:
        """Crée une conversation, renvoie son identifiant."""

    @abstractmethod
    def jouer_tour(
        self, conversation: str, texte: str
    ) -> AsyncIterator[Phrase | AppelOutilVu | FinTour]:
        """Joue un tour de dialogue : streame les `Phrase` à synthétiser (chacune
        avec sa voix courante) et les `AppelOutilVu` au fil de leur déclenchement,
        puis un `FinTour` final."""

    @abstractmethod
    async def interrompre(self, conversation: str, prefixe_prononce: str) -> None:
        """Signale au Dialogue Forge le préfixe réellement prononcé avant
        interruption, pour qu'il tronque son dernier tour (ADR 0012 décision 3)."""

    @abstractmethod
    async def clore(self, conversation: str) -> bool:
        """Clôt la conversation, déclenche la capture mémoire. Renvoie si un
        épisode a effectivement été capturé."""
