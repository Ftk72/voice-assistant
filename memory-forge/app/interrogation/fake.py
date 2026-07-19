"""Traducteur factice, déterministe, zéro réseau : aiguillage par mots-clés et
formulation par gabarit de phrase — pour les tests et le développement sans
LLM (même rôle que `GenerateurInsightFactice` côté insight)."""

import re

from app.interrogation.base import TraducteurQuestion
from app.schemas import Aiguillage, ContexteInterrogation

# Mots capitalisés en tête de question à ne pas prendre pour des entités.
_STOPWORDS = {
    "que", "qui", "quoi", "quel", "quelle", "quels", "quelles", "combien",
    "depuis", "quand", "comment", "pourquoi", "est", "sait", "on", "le", "la",
    "les", "un", "une", "de", "du", "des", "et", "ou", "il", "elle", "y",
}


def _mentions(question: str) -> list[str]:
    mots = re.findall(r"\b[A-ZÀ-Ý][\wà-ÿ-]*", question)
    vues: dict[str, str] = {}
    for mot in mots:
        if mot.lower() not in _STOPWORDS:
            vues.setdefault(mot.lower(), mot)
    return list(vues.values())


class TraducteurQuestionFactice(TraducteurQuestion):
    """Aiguillage par mots-clés (combien → compter, lien entre → lien_entre,
    quand → lecture_temporelle, sujet/touche → autour_du_sujet, sinon
    faits_sur) ; `cypher_libre` force le repli Cypher libre. Compte ses appels
    (`appels`) pour vérifier que le rejeu d'une requête n'en fait aucun."""

    def __init__(self, cypher_libre: str | None = None) -> None:
        self.appels = 0
        self._cypher_libre = cypher_libre

    async def aiguiller(
        self, question: str, contexte: ContexteInterrogation | None = None
    ) -> Aiguillage:
        self.appels += 1
        mentions = _mentions(question)
        if self._cypher_libre is not None:
            return Aiguillage(mentions=mentions, cypher=self._cypher_libre)
        q = question.lower()
        premiere = mentions[0] if mentions else None
        if "combien" in q:
            return Aiguillage(mentions=mentions, gabarit="compter", parametres={"sujet": premiere})
        if "lien" in q and len(mentions) >= 2:
            return Aiguillage(
                mentions=mentions,
                gabarit="lien_entre",
                parametres={"entite_a": mentions[0], "entite_b": mentions[1]},
            )
        if "quand" in q:
            return Aiguillage(
                mentions=mentions, gabarit="lecture_temporelle", parametres={"entite": premiere}
            )
        if "touche" in q or "autour" in q or "sujet" in q:
            dernier_mot = re.findall(r"[\wà-ÿ-]+", q)[-1] if re.findall(r"[\wà-ÿ-]+", q) else ""
            return Aiguillage(
                mentions=mentions,
                gabarit="autour_du_sujet",
                parametres={"sujet": premiere or dernier_mot},
            )
        return Aiguillage(mentions=mentions, gabarit="faits_sur", parametres={"entite": premiere})

    async def formuler(self, question: str, resultats: list[dict]) -> str:
        self.appels += 1
        apercu = " ; ".join(str(r) for r in resultats[:3])
        return f"D'après {len(resultats)} résultat(s) du graphe : {apercu}"
