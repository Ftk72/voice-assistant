from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MEMORY_FORGE_")

    host: str = "127.0.0.1"
    port: int = 8200
    backend: Literal["fake", "graphiti"] = "fake"
    # Utilisés uniquement par le backend graphiti :
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "memoryforge"
    llm_base_url: str = "http://llm:8080/v1"       # extraction (Qwen, différé)
    embedder_base_url: str = "http://embedder:8080/v1"  # bge-m3 CPU
