"""Canal réel — **jamais exécuté à ce jour** (pattern SystemPlayer).

Client HTTP du transport-voix (ticket wayfinder 0044). La chaîne complète :
time-forge ou action-forge POSTe son WAV sur `/play` du Pont hôte (elles
n'ont pas changé d'un octet et ignorent tout de l'état d'une conversation) →
le Pont demande ici `GET /conversation` au transport → si une conversation est
ouverte, il lui transfère le WAV par `POST /annonce`, que le transport injecte
dans le flux WebRTC sortant, seul endroit où l'annulation d'écho de la coquille
peut le voir et le soustraire du micro → sinon (409, transport muet, ou
injoignable) le Pont joue sur les enceintes comme avant.
"""

import httpx

from app.conversation.base import CanalConversation

# Le transport reste modeste : une annonce est courte et l'arbitrage est sur le
# chemin d'une annonce déjà en retard. Mieux vaut se replier vite sur les
# enceintes que faire attendre l'utilisateur.
_TIMEOUT_SECONDES = 3.0


class CanalTransportVoix(CanalConversation):
    """Interroge et alimente le transport-voix par HTTP."""

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    async def conversation_ouverte(self) -> bool:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=_TIMEOUT_SECONDES) as client:
            reponse = await client.get("/conversation")
            reponse.raise_for_status()
            return bool(reponse.json()["ouverte"])

    async def jouer_annonce(self, wav: bytes) -> bool:
        async with httpx.AsyncClient(base_url=self._base_url, timeout=_TIMEOUT_SECONDES) as client:
            reponse = await client.post(
                "/annonce", content=wav, headers={"Content-Type": "audio/wav"}
            )
            if reponse.status_code == 409:
                # Le transport a perdu sa session entre les deux appels : ce
                # n'est pas une panne, c'est un refus net — repli attendu.
                return False
            reponse.raise_for_status()
            return True
