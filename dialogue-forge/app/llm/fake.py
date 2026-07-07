"""Adaptateur LLM factice, scriptable par les tests. Aucun réseau."""

import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from app.llm.base import (
    AppelOutil,
    DefinitionOutil,
    DeltaTexte,
    EvenementLLM,
    Message,
    MoteurLLM,
)


@dataclass
class TourTexte:
    """Un tour scripté : le modèle répond du texte (streamé mot à mot)."""

    texte: str


@dataclass
class TourOutils:
    """Un tour scripté : le modèle demande un ou plusieurs appels d'outils."""

    appels: list[AppelOutil]


TourScripte = TourTexte | TourOutils


def _decouper_en_deltas(texte: str) -> list[str]:
    """Découpe un texte en petits fragments (mot + espace) pour simuler le flux."""
    fragments = re.findall(r"\S+\s*", texte)
    return fragments or ([texte] if texte else [])


@dataclass
class MoteurLLMFactice(MoteurLLM):
    """Moteur programmable. Chaque appel à `generer` consomme le prochain tour
    de `tours` ; une fois la liste épuisée, `tour_par_defaut` est rejoué (utile
    pour tester la boucle d'outils infinie et sa limite)."""

    tours: list[TourScripte] = field(default_factory=list)
    tour_par_defaut: TourScripte = field(default_factory=lambda: TourTexte("D'accord."))
    # Journal des appels : la liste des messages (copie) vus à chaque génération.
    appels_generation: list[list[Message]] = field(default_factory=list)

    async def generer(
        self, messages: list[Message], outils: list[DefinitionOutil]
    ) -> AsyncIterator[EvenementLLM]:
        self.appels_generation.append(list(messages))
        tour = self.tours.pop(0) if self.tours else self.tour_par_defaut
        if isinstance(tour, TourOutils):
            for appel in tour.appels:
                yield appel
        else:
            for fragment in _decouper_en_deltas(tour.texte):
                yield DeltaTexte(fragment)
