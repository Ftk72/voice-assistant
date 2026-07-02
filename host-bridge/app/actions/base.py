from abc import ABC, abstractmethod

from app.catalog import Action


class ActionRunner(ABC):
    """Port de l'exécuteur d'actions : lance une action du catalogue (jamais une
    commande arbitraire — le nom a déjà été validé contre la liste blanche) et
    renvoie un message de résultat parlable, que l'assistant confirme à l'oral."""

    @abstractmethod
    def run(self, action: Action) -> str: ...
