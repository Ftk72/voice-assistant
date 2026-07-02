"""Extraction du texte lisible d'une page HTML en stdlib pur — pas de moteur de
« readability » : pour une restitution vocale, retirer balisage, scripts et
menus suffit."""

import re
from html.parser import HTMLParser

# Conteneurs dont le contenu n'est jamais du texte à lire à voix haute.
_SKIPPED = {"script", "style", "noscript", "template", "nav", "header", "footer", "aside", "svg"}
_BLOCKS = {"p", "div", "li", "br", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "section", "article"}
# Sépare les blocs sans se confondre avec les retours à la ligne du source HTML
# (qui, eux, valent une simple espace à l'intérieur d'un paragraphe).
_BLOCK_BREAK = "\x00"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._chunks: list[str] = []
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in _SKIPPED:
            self._skip_depth += 1
        elif tag == "title":
            self._in_title = True
        elif tag in _BLOCKS:
            self._chunks.append(_BLOCK_BREAK)

    def handle_endtag(self, tag: str) -> None:
        if tag in _SKIPPED and self._skip_depth:
            self._skip_depth -= 1
        elif tag == "title":
            self._in_title = False
        elif tag in _BLOCKS:
            self._chunks.append(_BLOCK_BREAK)

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self.title += data
        elif not self._skip_depth:
            self._chunks.append(data)


def extract_text(html: str) -> tuple[str, str]:
    """(titre, texte) : lignes non vides, espaces normalisés."""
    parser = _TextExtractor()
    parser.feed(html)
    raw_blocks = "".join(parser._chunks).split(_BLOCK_BREAK)
    blocks = [re.sub(r"\s+", " ", block).strip() for block in raw_blocks]
    return parser.title.strip(), "\n".join(block for block in blocks if block)
