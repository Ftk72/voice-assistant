from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Le dossier des personas vit à la racine du dépôt, deux niveaux au-dessus de app/.
PERSONAS_PAR_DEFAUT = Path(__file__).resolve().parent.parent.parent / "personas"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DIALOGUE_FORGE_")

    host: str = "127.0.0.1"
    port: int = 8600

    # Moteur LLM — llama.cpp expose une API compatible OpenAI.
    llm_backend: Literal["fake", "openai"] = "fake"
    llm_base_url: str = "http://127.0.0.1:8001/v1"
    llm_model: str = "local"

    # Mémoire — memory-forge (injection avant le tour, extraction après).
    memoire_backend: Literal["fake", "rest"] = "fake"
    memory_forge_url: str = "http://127.0.0.1:8200"

    # Outils — le forge est *client* MCP (il n'expose aucun serveur MCP).
    outils_backend: Literal["fake", "mcp"] = "fake"
    mcp_urls: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:8400/mcp",  # time-forge
            "http://127.0.0.1:8300/mcp",  # world-forge
            "http://127.0.0.1:8200/mcp",  # memory-forge
        ]
    )

    # Personas et boucle d'outils.
    personas_dir: Path = PERSONAS_PAR_DEFAUT
    persona_defaut: str = "assistant"
    max_iterations_outils: int = 5
