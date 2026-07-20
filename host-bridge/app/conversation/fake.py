from dataclasses import dataclass, field

from app.conversation.base import CanalConversation


@dataclass
class CanalFactice(CanalConversation):
    """Canal factice : aucun réseau, garde les wav reçus — tests et dev sans
    transport. `ouverte` est False par défaut, donc le comportement nominal du
    Pont reste « sur les enceintes », comme avant le ticket 0044 ; `accepte`
    permet de simuler un transport qui refuse (session perdue entre-temps)."""

    ouverte: bool = False
    accepte: bool = True
    annonces: list[bytes] = field(default_factory=list)

    async def conversation_ouverte(self) -> bool:
        return self.ouverte

    async def jouer_annonce(self, wav: bytes) -> bool:
        if not self.ouverte or not self.accepte:
            return False
        self.annonces.append(wav)
        return True
