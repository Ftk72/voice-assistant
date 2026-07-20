"""Gestionnaire des Tâches (contrat 0031) : Tâches en mémoire process, une
Tâche = une boucle CodeAct dans son propre Atelier, lancée en tâche asyncio.
Publie les événements de la boucle sur une file par Tâche pour le flux SSE."""

import asyncio
import logging
from collections.abc import AsyncIterator, Callable
from contextlib import suppress
from uuid import uuid4

from app.annonce.base import Annonceur
from app.atelier.base import Atelier
from app.boucle import BoucleCodeAct, EvenementBoucle
from app.schemas import Tache

logger = logging.getLogger(__name__)

# Sentinelle de fin de flux (distincte de tout événement réel).
_FIN_DE_FLUX = None


class GestionnaireTaches:
    def __init__(
        self,
        atelier_factory: Callable[[], Atelier],
        boucle: BoucleCodeAct,
        annonceur: Annonceur,
    ) -> None:
        self._atelier_factory = atelier_factory
        self._boucle = boucle
        self._annonceur = annonceur
        self._taches: dict[str, Tache] = {}
        self._tasks: dict[str, asyncio.Task] = {}
        self._files: dict[str, asyncio.Queue[EvenementBoucle | None]] = {}
        self._ordre: list[str] = []

    def confier(self, enonce: str) -> Tache:
        tache = Tache(id=str(uuid4()), enonce=enonce)
        self._taches[tache.id] = tache
        self._ordre.append(tache.id)
        self._files[tache.id] = asyncio.Queue()
        self._tasks[tache.id] = asyncio.create_task(self._executer(tache))
        return tache

    def obtenir(self, tache_id: str) -> Tache | None:
        return self._taches.get(tache_id)

    def lister(self) -> list[Tache]:
        return list(self._taches.values())

    def derniere_en_cours(self) -> Tache | None:
        """La Tâche en cours la plus récente (l'utilisateur ne dit jamais un
        identifiant à voix haute) — sert de défaut aux outils MCP."""
        for tache_id in reversed(self._ordre):
            tache = self._taches[tache_id]
            if tache.statut == "en_cours":
                return tache
        return None

    async def attendre_fin(self, tache_id: str) -> None:
        """Attend la fin de la Tâche `tache_id` (utilitaire de test/synchronisation)."""
        task = self._tasks.get(tache_id)
        if task is None:
            return
        with suppress(asyncio.CancelledError):
            await task

    async def annuler(self, tache_id: str) -> bool:
        task = self._tasks.get(tache_id)
        if task is None or task.done():
            return False
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        return True

    async def flux(self, tache_id: str) -> AsyncIterator[EvenementBoucle]:
        """Streame les événements de la boucle pour `tache_id` jusqu'à sa fin
        (Tâche déjà terminée : le flux se ferme immédiatement, sans événement)."""
        if tache_id not in self._files:
            raise KeyError(tache_id)
        file = self._files[tache_id]
        while True:
            evenement = await file.get()
            if evenement is _FIN_DE_FLUX:
                return
            yield evenement

    async def _executer(self, tache: Tache) -> None:
        atelier = self._atelier_factory()
        file = self._files[tache.id]

        async def publier(evenement: EvenementBoucle) -> None:
            await file.put(evenement)

        try:
            await atelier.demarrer(tache.id)
            await self._boucle.executer(tache, atelier, sur_evenement=publier)
        except asyncio.CancelledError:
            tache.statut = "annulee"
            tache.compte_rendu = "Tâche annulée."
            raise
        finally:
            await atelier.detruire()
            await file.put(_FIN_DE_FLUX)
            await self._annoncer_issue(tache)

    async def _annoncer_issue(self, tache: Tache) -> None:
        """Annonce l'issue une fois la Tâche dans un état terminal — jamais pour
        une annulation (l'utilisateur vient de la demander, il le sait), et une
        annonce en échec ne doit jamais empêcher la Tâche de se conclure."""
        if tache.statut == "terminee":
            texte = f"J'ai terminé : {tache.compte_rendu}"
        elif tache.statut == "echouee":
            texte = f"Je n'ai pas réussi : {tache.compte_rendu}"
        else:
            return
        try:
            await self._annonceur.annoncer(texte)
        except Exception:
            logger.exception("Échec de l'annonce de fin de Tâche %s", tache.id)
