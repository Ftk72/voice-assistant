"""Adaptateur mémoire factice. Aucun réseau."""

from dataclasses import dataclass, field

from app.memoire.base import MoteurMemoire


@dataclass
class EpisodeCapture:
    contenu: str
    nom: str


@dataclass
class MemoireFactice(MoteurMemoire):
    """Mémoire programmable : `faits` est renvoyé tel quel à toute recherche ;
    les épisodes capturés sont journalisés dans `episodes` pour les tests."""

    faits: list[str] = field(default_factory=list)
    episodes: list[EpisodeCapture] = field(default_factory=list)

    async def rechercher(self, question: str) -> list[str]:
        return list(self.faits)

    async def capturer_episode(self, contenu: str, nom: str) -> None:
        self.episodes.append(EpisodeCapture(contenu=contenu, nom=nom))
