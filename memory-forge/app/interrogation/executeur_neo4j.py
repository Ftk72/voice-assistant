"""Adaptateur réel : exécution des requêtes du canal d'interrogation sur Neo4j
(ticket wayfinder 0028).

**Exécuté au réel le 2026-07-19** (validation à l'œil du ticket 0028 sur le
corpus synthétique, Neo4j de la stack compose).

Garde-fous d'exécution (les garde-fous textuels vivent dans garde_fous.py) :
session en lecture seule (`READ_ACCESS`) et timeout par requête.
"""

from app.config import Settings
from app.interrogation.executeur import ExecuteurCypher
from app.schemas import RequeteCypher

DELAI_REQUETE_SECONDES = 10.0


def _valeur_sure(valeur):
    """Valeurs JSON-sérialisables : les temporels du driver (`neo4j.time.*`)
    passent par `to_native()` puis isoformat, les listes se convertissent
    membre à membre, le reste inconnu devient sa représentation texte."""
    if hasattr(valeur, "to_native"):
        valeur = valeur.to_native()
    if hasattr(valeur, "isoformat"):
        return valeur.isoformat()
    if isinstance(valeur, list):
        return [_valeur_sure(v) for v in valeur]
    if valeur is None or isinstance(valeur, str | int | float | bool):
        return valeur
    return str(valeur)


class ExecuteurCypherNeo4j(ExecuteurCypher):
    """Session lecture seule + timeout sur le Neo4j de la stack (mêmes
    réglages de connexion que le backend graphiti)."""

    def __init__(self, settings: Settings) -> None:
        try:
            from neo4j import AsyncGraphDatabase
        except ImportError as error:
            raise RuntimeError(
                "le driver neo4j n'est pas installé — lancer : uv sync --extra graphiti"
            ) from error
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
        )

    async def executer(self, requete: RequeteCypher) -> list[dict]:
        from neo4j import READ_ACCESS, Query

        async with self._driver.session(default_access_mode=READ_ACCESS) as session:
            resultat = await session.run(
                Query(requete.cypher, timeout=DELAI_REQUETE_SECONDES),  # type: ignore[arg-type]
                dict(requete.parametres),
            )
            lignes = await resultat.data()
        return [{cle: _valeur_sure(v) for cle, v in ligne.items()} for ligne in lignes]

    async def aclose(self) -> None:
        await self._driver.close()
