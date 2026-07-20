from abc import ABC, abstractmethod


class CanalConversation(ABC):
    """Port du canal de conversation : dit au Pont hôte si une conversation est
    ouverte, et sait lui confier une annonce pour qu'elle sorte par ce canal
    plutôt que par les enceintes (ticket wayfinder 0044).

    Raison d'être : la parole de conversation sort par la coquille en WebRTC,
    dont la pile annule l'écho de ce qu'elle rend elle-même ; une annonce jouée
    sur les enceintes échappe à cette annulation, rentre par le micro, et
    l'assistant répond à sa propre voix. Le Pont hôte arbitre — c'est lui qui
    joue déjà le son, une seule forge apprend donc l'état d'une conversation."""

    @abstractmethod
    async def conversation_ouverte(self) -> bool:
        """Une conversation est-elle ouverte (micro vif) ?"""

    @abstractmethod
    async def jouer_annonce(self, wav: bytes) -> bool:
        """Confie le wav au canal. True = pris en charge (l'annonce est partie
        dans la conversation, les enceintes ne doivent pas le rejouer)."""
