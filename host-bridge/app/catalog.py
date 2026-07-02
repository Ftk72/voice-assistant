"""Le catalogue d'actions : la liste blanche fermée (CONTEXT.md § Actions).
Chaque action est nommée et décrite par l'utilisateur dans un TOML ; l'assistant
ne peut rien exécuter d'autre — jamais de commande arbitraire."""

import tomllib
from pathlib import Path

from pydantic import BaseModel


class Action(BaseModel):
    """Une entrée du catalogue. La commande est un argv explicite (jamais un shell),
    déclinée par plateforme : la cible visée est Windows, le dev se fait sous Linux."""

    name: str
    description: str
    windows: list[str] | None = None
    linux: list[str] | None = None

    def command_for(self, platform: str) -> list[str] | None:
        return self.windows if platform.startswith("win") else self.linux


def load_catalog(path: Path) -> dict[str, Action]:
    if not path.exists():
        return {}
    with path.open("rb") as file:
        data = tomllib.load(file)
    catalog: dict[str, Action] = {}
    for name, entry in data.get("actions", {}).items():
        catalog[name] = Action(name=name, **entry)
    return catalog
