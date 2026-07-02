from datetime import UTC, datetime

from app.config import Settings
from app.graph.base import GraphMemory
from app.schemas import EpisodeIn, Fact, Provenance


class GraphitiMemory(GraphMemory):
    """Adaptateur Graphiti + Neo4j (ADR 0005).

    ⚠️ Écrit d'après la documentation de graphiti-core, jamais exécuté (dépendances
    non installées à l'écriture — connexion lente). À valider au premier lancement
    réel, comme _RealChatterboxEngine côté voice-forge.
    """

    def __init__(self, settings: Settings) -> None:
        try:
            from graphiti_core import Graphiti
            from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
            from graphiti_core.llm_client.config import LLMConfig
            from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
        except ImportError as error:
            raise RuntimeError(
                "graphiti-core n'est pas installé — lancer : uv sync --extra graphiti"
            ) from error

        self._graphiti = Graphiti(
            settings.neo4j_uri,
            settings.neo4j_user,
            settings.neo4j_password,
            llm_client=OpenAIGenericClient(
                config=LLMConfig(api_key="sk-local", base_url=settings.llm_base_url)
            ),
            embedder=OpenAIEmbedder(
                config=OpenAIEmbedderConfig(
                    api_key="sk-local", base_url=settings.embedder_base_url
                )
            ),
        )

    async def add_episode(self, episode: EpisodeIn) -> None:
        from graphiti_core.nodes import EpisodeType

        await self._graphiti.add_episode(
            name=episode.name,
            episode_body=episode.content,
            source=EpisodeType.message if episode.source == "conversation" else EpisodeType.text,
            source_description=f"{episode.source}:{episode.name}",
            reference_time=datetime.now(UTC),
        )

    async def search(self, query: str) -> list[Fact]:
        edges = await self._graphiti.search(query)
        return [
            Fact(
                text=edge.fact,
                # La provenance fine (nom d'épisode) demande une passe de plus ;
                # on renvoie la description de source au premier niveau.
                provenance=Provenance(source="conversation", name=edge.source_node_uuid),
                valid_at=edge.valid_at,
                invalid_at=edge.invalid_at,
            )
            for edge in edges
        ]

    async def forget(self, entity: str) -> int:
        """Suppression réelle des nœuds dont le nom correspond, et de leurs relations."""
        records, _, _ = await self._graphiti.driver.execute_query(
            """
            MATCH (n:Entity) WHERE toLower(n.name) CONTAINS toLower($entity)
            DETACH DELETE n
            RETURN count(n) AS deleted
            """,
            entity=entity,
        )
        return records[0]["deleted"] if records else 0
