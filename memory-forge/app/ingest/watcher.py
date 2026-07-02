"""Surveillance du dossier `documents/` par polling mtime : fiable sur les
bind-mounts WSL/Docker où inotify ne remonte pas les événements de l'hôte."""

import json
from pathlib import Path

from app.ingest.chunker import chunk_document
from app.schemas import EpisodeIn

STATE_FILE = ".memory-forge-state.json"


class DocumentWatcher:
    """Détecte les documents nouveaux ou modifiés ; l'état (mtime par fichier) est
    persisté dans le dossier surveillé pour survivre aux redémarrages."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._state_path = directory / STATE_FILE

    def scan_once(self) -> list[EpisodeIn]:
        """Épisodes des documents nouveaux ou modifiés depuis le dernier scan."""
        state = self._load_state()
        episodes: list[EpisodeIn] = []
        for path in sorted(self._directory.iterdir()):
            if not path.is_file() or path.name.startswith("."):
                continue
            mtime = path.stat().st_mtime
            if state.get(path.name) != mtime:
                episodes.extend(chunk_document(path))
                state[path.name] = mtime
        self._save_state(state)
        return episodes

    def _load_state(self) -> dict[str, float]:
        if self._state_path.exists():
            return json.loads(self._state_path.read_text(encoding="utf-8"))
        return {}

    def _save_state(self, state: dict[str, float]) -> None:
        self._state_path.write_text(json.dumps(state), encoding="utf-8")
