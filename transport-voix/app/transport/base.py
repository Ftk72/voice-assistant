"""Port de la couche transport temps réel (Pipecat/WebRTC)."""

from abc import ABC, abstractmethod


class Transport(ABC):
    """Établit la session temps réel avec la webview de la coquille (WebRTC) :
    pousse l'audio du micro vers le STT et rejoue l'audio produit par le TTS."""

    @abstractmethod
    async def demarrer(self) -> None:
        """Établit la session temps réel."""

    @abstractmethod
    async def arreter(self) -> None:
        """Termine la session temps réel."""

    # --- Annonces spontanées (ticket wayfinder 0044) -------------------------
    # Concrètes, pas abstraites : les implémentations qui n'ont pas de session à
    # offrir (transports de test, adaptateurs futurs) héritent d'un refus poli
    # et le Pont hôte se rabat alors sur les enceintes.

    def conversation_ouverte(self) -> bool:
        """Une session temps réel est-elle en cours ?

        Le Pont hôte pose cette question avant de jouer une annonce (fin de
        Tâche, échéance de minuteur) : si une conversation est ouverte, le micro
        est vif et une annonce sortie sur les enceintes rentrerait par lui."""
        return False

    async def jouer_annonce(self, wav: bytes) -> bool:
        """Injecte `wav` dans le flux sortant de la session en cours.

        C'est **le passage par le flux sortant** qui rend l'annonce visible à
        l'annulation d'écho acoustique de la coquille : l'AEC ne sait soustraire
        du micro que ce qu'elle a elle-même rendu. Une annonce jouée hors de ce
        flux (enceintes, Pont hôte) lui est structurellement invisible — elle est
        alors captée, transcrite, et l'assistant répond à sa propre voix.

        Renvoie False si aucune session ne peut la jouer (l'appelant se replie
        sur les enceintes : mieux vaut un écho qu'un silence)."""
        return False
