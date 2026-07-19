from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="MEMORY_FORGE_")

    host: str = "127.0.0.1"
    port: int = 8200
    backend: Literal["fake", "graphiti"] = "fake"
    # Récit du graphe mémoire (ticket wayfinder 0020) : le réel réutilise llm_base_url.
    insight_backend: Literal["fake", "openai"] = "fake"
    # Interrogation façon LinkQ (ticket 0028) : le réel réutilise llm_base_url ;
    # l'exécuteur Cypher, lui, suit `backend` (graphiti → Neo4j, sinon factice).
    interrogation_backend: Literal["fake", "openai"] = "fake"
    # Ingestion documentaire (phase 4) — désactivée si aucun dossier n'est fourni.
    documents_dir: Path | None = None
    documents_poll_seconds: float = 10.0  # polling mtime, fiable sur bind-mounts WSL
    # Utilisés uniquement par le backend graphiti :
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "memoryforge"
    llm_base_url: str = "http://llm:8080/v1"       # extraction (Qwen, différé)
    embedder_base_url: str = "http://embedder:8080/v1"  # bge-m3 CPU
