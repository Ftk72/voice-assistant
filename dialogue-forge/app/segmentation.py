"""Segmentation d'un flux de texte en phrases, pour la synthèse vocale.

Le TTS en aval synthétise phrase par phrase : on découpe sur `.`, `!`, `?`, `…`
suivis d'une espace (ou de la fin du flux). La ponctuation prise entre deux
chiffres n'est pas une fin de phrase — les nombres « 2,88 » (virgule, jamais une
fin) comme « 3.14 » (point décimal) restent intacts.
"""

import re

_FIN = re.compile(r"[.!?…]+")


class SegmenteurPhrases:
    """Segmenteur incrémental : on `absorber` des fragments au fil du flux, ce
    qui renvoie les phrases déjà complètes ; `terminer` vide le reste."""

    def __init__(self) -> None:
        self._tampon = ""

    def absorber(self, fragment: str) -> list[str]:
        self._tampon += fragment
        phrases: list[str] = []
        while True:
            phrase = self._detacher_une_phrase()
            if phrase is None:
                break
            if phrase:
                phrases.append(phrase)
        return phrases

    def terminer(self) -> list[str]:
        reste = self._tampon.strip()
        self._tampon = ""
        return [reste] if reste else []

    def _detacher_une_phrase(self) -> str | None:
        """Détache la première phrase complète du tampon, ou None s'il faut
        attendre la suite du flux. Une chaîne vide signale une coupure blanche
        (à ignorer) tout en ayant progressé."""
        for correspondance in _FIN.finditer(self._tampon):
            debut, fin = correspondance.start(), correspondance.end()
            # Ponctuation entre deux chiffres (ex. « 3.14 ») : pas une fin.
            if (
                debut > 0
                and fin < len(self._tampon)
                and self._tampon[debut - 1].isdigit()
                and self._tampon[fin].isdigit()
            ):
                continue
            if fin == len(self._tampon):
                # Terminateur en fin de tampon : attendre le caractère suivant
                # (il pourrait s'agir d'un point décimal, ou d'autres signes).
                return None
            if self._tampon[fin].isspace():
                phrase = self._tampon[:fin].strip()
                self._tampon = self._tampon[fin:].lstrip()
                return phrase
        return None
