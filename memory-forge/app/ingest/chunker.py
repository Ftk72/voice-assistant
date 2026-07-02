"""Découpage des documents en épisodes (cf. CONTEXT.md : un épisode = un fragment
de document). Markdown : une section par titre ; le graphe relie les fragments
entre eux via les entités partagées."""

import re
from pathlib import Path

from app.schemas import EpisodeIn


def _chunk_markdown(path: Path) -> list[EpisodeIn]:
    text = path.read_text(encoding="utf-8")
    episodes: list[EpisodeIn] = []
    title = None
    lines: list[str] = []

    def flush() -> None:
        content = "\n".join(lines).strip()
        if content:
            name = f"{path.name} § {title}" if title else path.name
            episodes.append(EpisodeIn(content=content, source="document", name=name))
        lines.clear()

    for line in text.splitlines():
        heading = re.match(r"#{1,6}\s+(.+)", line)
        if heading:
            flush()
            title = heading.group(1).strip()
        else:
            lines.append(line)
    flush()
    return episodes


def _chunk_pdf(path: Path) -> list[EpisodeIn]:
    from pypdf import PdfReader

    episodes = []
    for number, page in enumerate(PdfReader(path).pages, start=1):
        content = page.extract_text().strip()
        if content:
            episodes.append(
                EpisodeIn(content=content, source="document", name=f"{path.name} p.{number}")
            )
    return episodes


def chunk_document(path: Path) -> list[EpisodeIn]:
    """Épisodes d'un document ; un format inconnu ne produit rien."""
    if path.suffix.lower() in {".md", ".markdown"}:
        return _chunk_markdown(path)
    if path.suffix.lower() == ".pdf":
        return _chunk_pdf(path)
    return []
