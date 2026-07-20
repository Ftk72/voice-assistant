"""Smoke test réel (ticket 0033) : hors du `pytest` par défaut (celui-ci reste vert
sans Docker, cf. `app/atelier/fake.py`). Nécessite `uv sync --extra docker`, le
socket Docker monté et l'image `action-forge-atelier:latest` construite ; se lance
explicitement :

    ACTION_FORGE_SMOKE_DOCKER=1 uv run --extra docker pytest tests/test_atelier_docker.py
"""

import os

import pytest

pytest.importorskip("docker")

pytestmark = pytest.mark.skipif(
    os.environ.get("ACTION_FORGE_SMOKE_DOCKER") != "1",
    reason="smoke test réel — ACTION_FORGE_SMOKE_DOCKER=1 pour le lancer",
)


async def test_l_atelier_docker_lance_borne_et_detruit_un_conteneur_reel(tmp_path):
    from app.atelier.docker import AtelierDocker
    from app.config import Settings

    dossier_tache = tmp_path / "tache-smoke"
    dossier_tache.mkdir()
    settings = Settings(atelier_backend="docker", echange_dir_hote=str(tmp_path))

    atelier = AtelierDocker(settings)
    await atelier.demarrer("tache-smoke")
    try:
        resultat = await atelier.executer("echo bonjour de l atelier")
        assert resultat.code_retour == 0
        assert "bonjour" in resultat.sortie_standard
    finally:
        await atelier.detruire()

    import docker as docker_sdk

    client = docker_sdk.from_env()
    filtre = {"label": "action-forge.tache=tache-smoke"}
    conteneurs = client.containers.list(all=True, filters=filtre)
    assert conteneurs == []


async def test_nettoyer_orphelins_detruit_un_conteneur_d_atelier_oublie():
    from app.atelier.docker import LABEL_TACHE, nettoyer_orphelins
    from app.config import Settings

    settings = Settings(atelier_backend="docker")
    import docker as docker_sdk

    client = docker_sdk.from_env()
    orphelin = client.containers.run(
        settings.atelier_image,
        command="sleep infinity",
        detach=True,
        network_disabled=True,
        labels={LABEL_TACHE: "tache-orpheline"},
    )
    try:
        await nettoyer_orphelins()
        assert client.containers.list(all=True, filters={"id": orphelin.id}) == []
    finally:
        from contextlib import suppress

        with suppress(docker_sdk.errors.NotFound):
            orphelin.remove(force=True)
