from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ACTION_FORGE_")

    host: str = "127.0.0.1"
    port: int = 8800
    atelier_backend: Literal["fake", "docker"] = "fake"
    # Image fixe de l'Atelier (contrat 0031) : jamais choisie par la Tâche.
    atelier_image: str = "action-forge-atelier:latest"
    atelier_cpus: float = 1.0
    atelier_memoire_mo: int = 512
    atelier_timeout_secondes: float = 30.0
    llm_backend: Literal["fake", "openai"] = "fake"
    llm_base_url: str = "http://127.0.0.1:8001/v1"
    llm_model: str = "local"
    # Budget de pas de la boucle CodeAct (contrat 0031 : budget borné, échec propre).
    budget_pas: int = 8
    # Chemin HÔTE (pas celui, interne, de la forge conteneurisée) du dossier
    # d'échange : le socket Docker fait créer les Ateliers par le daemon hôte,
    # qui résout les montages depuis le système de fichiers hôte (ADR 0013).
    echange_dir_hote: str = "/echange-atelier"
    annonceur: Literal["journal", "pont_hote"] = "journal"
    # Utilisés uniquement par l'annonceur pont_hote :
    voice_forge_url: str = "http://127.0.0.1:8100"
    annonce_voix: str = "Jackie"
    # Le Pont hôte tourne sur la machine hôte, hors Docker (ADR 0008).
    host_bridge_url: str = "http://127.0.0.1:8500"
    # Jeton partagé attendu par le Pont (vide = Pont sans auth, dev local).
    host_bridge_token: str = ""
