"""Chargement des personas au format existant du dépôt (voir personas/README.md).

Un persona est un fichier `*.md` (hors README) dont :
- le titre `# Nom (voix : X)` donne le nom et la voix, avec un jeton optionnel
  `, off-record` après la voix (`# Nom (voix : X, off-record)`) qui marque un
  persona dont les conversations ne sont jamais mémorisées (ADR 0011),
- le premier bloc de code clôturé (``` … ```) donne le prompt système.

Un fichier mal formé (titre ou bloc absent) est ignoré proprement.
"""

import re
from dataclasses import dataclass
from pathlib import Path

# La voix s'arrête à la virgule (ou à la parenthèse) : le jeton « off-record »
# vient éventuellement après, sans polluer le nom de la voix.
_TITRE = re.compile(
    r"^#\s*(?P<nom>.+?)\s*\(\s*voix\s*:\s*(?P<voix>[^,)]+?)\s*"
    r"(?P<offrecord>,\s*off-record)?\s*\)\s*$",
    re.MULTILINE,
)
_BLOC_CODE = re.compile(r"```[^\n]*\n(?P<corps>.*?)```", re.DOTALL)


@dataclass(frozen=True)
class Persona:
    nom: str
    voix: str
    prompt: str
    off_record: bool = False


def _analyser(texte: str) -> Persona | None:
    titre = _TITRE.search(texte)
    bloc = _BLOC_CODE.search(texte)
    if titre is None or bloc is None:
        return None
    prompt = bloc.group("corps").strip()
    if not prompt:
        return None
    return Persona(
        nom=titre.group("nom").strip(),
        voix=titre.group("voix").strip(),
        prompt=prompt,
        off_record=titre.group("offrecord") is not None,
    )


def charger_personas(dossier: Path) -> dict[str, Persona]:
    """Renvoie les personas trouvés dans `dossier`, indexés par nom en minuscules
    (clé de sélection). Dossier absent ou fichiers mal formés : ignorés."""
    personas: dict[str, Persona] = {}
    if not dossier.is_dir():
        return personas
    for chemin in sorted(dossier.glob("*.md")):
        if chemin.stem.lower() == "readme":
            continue
        persona = _analyser(chemin.read_text(encoding="utf-8"))
        if persona is not None:
            personas[persona.nom.lower()] = persona
    return personas
