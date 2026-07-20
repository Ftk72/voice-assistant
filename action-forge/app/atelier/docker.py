"""Adaptateur réel — premier run réel le 2026-07-20 (smoke test du ticket 0033,
lancement/exécution/destruction d'un conteneur au réel) : pilote des conteneurs
Docker jetables frères via le socket monté dans la forge (ADR 0013). Le socket
n'est monté QUE dans la forge — jamais dans l'Atelier lui-même — et le seul
montage de l'Atelier est le sous-dossier d'échange de sa Tâche."""

import asyncio
import time

import docker
from docker.errors import DockerException, NotFound
from docker.types import Mount

from app.atelier.base import Atelier, AtelierIndisponible
from app.config import Settings
from app.schemas import ActionResultat

LABEL_TACHE = "action-forge.tache"


class AtelierDocker(Atelier):
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = docker.from_env()
        self._conteneur = None

    async def demarrer(self, tache_id: str) -> None:
        montage_hote = f"{self._settings.echange_dir_hote.rstrip('/')}/{tache_id}"
        try:
            self._conteneur = await asyncio.to_thread(
                self._client.containers.run,
                self._settings.atelier_image,
                command="sleep infinity",
                detach=True,
                network_disabled=True,
                mem_limit=f"{self._settings.atelier_memoire_mo}m",
                nano_cpus=int(self._settings.atelier_cpus * 1_000_000_000),
                mounts=[Mount(target="/echange", source=montage_hote, type="bind")],
                labels={LABEL_TACHE: tache_id},
            )
        except DockerException as exc:
            raise AtelierIndisponible(f"démarrage de l'Atelier impossible : {exc}") from exc

    async def executer(self, code: str) -> ActionResultat:
        if self._conteneur is None:
            raise AtelierIndisponible("l'Atelier n'est pas démarré")
        debut = time.monotonic()
        commande = [
            "timeout",
            str(int(self._settings.atelier_timeout_secondes)),
            "bash",
            "-c",
            code,
        ]
        try:
            code_retour, sortie = await asyncio.to_thread(
                self._conteneur.exec_run, commande, demux=True
            )
        except DockerException as exc:
            raise AtelierIndisponible(f"exécution impossible dans l'Atelier : {exc}") from exc
        stdout, stderr = sortie
        return ActionResultat(
            sortie_standard=(stdout or b"").decode(errors="replace"),
            erreur_standard=(stderr or b"").decode(errors="replace"),
            code_retour=code_retour,
            duree_secondes=time.monotonic() - debut,
        )

    async def detruire(self) -> None:
        if self._conteneur is None:
            return
        try:
            await asyncio.to_thread(self._conteneur.remove, force=True)
        except NotFound:
            pass
        finally:
            self._conteneur = None


async def nettoyer_orphelins() -> None:
    """Détruit au démarrage tout conteneur d'Atelier resté du process précédent
    (crash, redémarrage) — promis par l'ADR 0013 (§ « Éphémère au palier 1 »)."""
    client = docker.from_env()
    orphelins = await asyncio.to_thread(
        client.containers.list, all=True, filters={"label": LABEL_TACHE}
    )
    for conteneur in orphelins:
        await asyncio.to_thread(conteneur.remove, force=True)
