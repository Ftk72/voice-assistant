from abc import ABC, abstractmethod

from app.schemas import RequeteCypher


class ExecuteurCypher(ABC):
    """Port de l'exécution des requêtes du canal d'interrogation (ticket 0028).
    Le réel vit dans executeur_neo4j.py ; le factice ci-dessous sert les tests
    et le backend `fake` (sans Neo4j, il ne trouve jamais rien)."""

    @abstractmethod
    async def executer(self, requete: RequeteCypher) -> list[dict]:
        """Les lignes de résultat, en valeurs JSON-sérialisables."""


class ExecuteurCypherFactice(ExecuteurCypher):
    """Renvoie des résultats préparés et journalise chaque requête reçue
    (`requetes`) — les tests y lisent ce qui serait parti vers Neo4j."""

    def __init__(self, resultats: list[dict] | None = None) -> None:
        self.resultats = resultats or []
        self.requetes: list[RequeteCypher] = []

    async def executer(self, requete: RequeteCypher) -> list[dict]:
        self.requetes.append(requete)
        return list(self.resultats)
