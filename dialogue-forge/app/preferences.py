"""Préférence permanente de réglage grand public (persona + voix par défaut,
ticket wayfinder 0014, modèle A) : toute nouvelle conversation créée **sans
persona explicite** adopte le persona et la voix ici enregistrés."""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Preferences:
    persona: str
    voix: str | None = None


def charger_preferences(chemin: Path, persona_defaut: str) -> Preferences:
    """Lit la préférence enregistrée dans `chemin`. Fichier absent, illisible ou
    corrompu : replie proprement sur `persona_defaut` sans voix."""
    if chemin.is_file():
        try:
            donnees = json.loads(chemin.read_text(encoding="utf-8"))
            return Preferences(persona=donnees["persona"], voix=donnees.get("voix"))
        except (OSError, ValueError, KeyError):
            logger.warning("Préférence illisible ou corrompue (%s) : repli sur le défaut", chemin)
    return Preferences(persona=persona_defaut, voix=None)


def enregistrer_preferences(chemin: Path, prefs: Preferences) -> None:
    """Persiste la préférence, en créant le dossier parent si besoin."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(asdict(prefs), ensure_ascii=False), encoding="utf-8")
