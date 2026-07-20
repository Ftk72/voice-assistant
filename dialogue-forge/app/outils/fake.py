"""Adaptateur outils factice. Aucun réseau."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from app.llm.base import DefinitionOutil
from app.outils.base import MoteurOutils

# Un résultat programmé : soit une chaîne fixe, soit une fonction des arguments.
Resultat = str | Callable[[dict[str, Any]], str]


@dataclass
class OutilsFactices(MoteurOutils):
    """Outils programmables : `definitions` est renvoyé à `lister_outils`,
    `resultats` (nom → chaîne ou fonction) répond aux appels. `appels`
    journalise chaque invocation pour les tests."""

    definitions: list[DefinitionOutil] = field(default_factory=list)
    resultats: dict[str, Resultat] = field(default_factory=dict)
    appels: list[tuple[str, dict[str, Any]]] = field(default_factory=list)
    appels_lister_outils: int = 0
    # File programmable des réponses successives de `rafraichir` : chaque appel
    # dépile la tête de liste (None = « rien n'a changé »). Épuisée, `rafraichir`
    # renvoie None. Permet aux tests de simuler une reprise sans réseau.
    rafraichissements: list[list[DefinitionOutil] | None] = field(default_factory=list)
    appels_rafraichir: int = 0

    async def lister_outils(self) -> list[DefinitionOutil]:
        self.appels_lister_outils += 1
        return list(self.definitions)

    async def appeler(self, nom: str, arguments: dict[str, Any]) -> str:
        self.appels.append((nom, arguments))
        resultat = self.resultats.get(nom, "")
        return resultat(arguments) if callable(resultat) else str(resultat)

    async def rafraichir(self) -> list[DefinitionOutil] | None:
        self.appels_rafraichir += 1
        if not self.rafraichissements:
            return None
        return self.rafraichissements.pop(0)
