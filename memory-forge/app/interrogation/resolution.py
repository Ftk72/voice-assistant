"""Ancrage anti-hallucination (ticket wayfinder 0028) : les mentions d'entités
extraites par le LLM se résolvent **côté serveur** contre les vrais noms de
nœuds du graphe — en flou (casse, accents, sous-chaîne), en pur Python. Une
mention qui ne se résout pas remonte au monologue au lieu d'entrer dans la
requête."""

import unicodedata

from app.schemas import MentionResolue


def _normaliser(texte: str) -> str:
    """Minuscules, sans accents, tirets ramenés à l'espace : « Léa » ≡ « lea »,
    « jules ferry » ≡ « Jules-Ferry »."""
    decompose = unicodedata.normalize("NFKD", texte.casefold())
    plat = "".join(c for c in decompose if not unicodedata.combining(c))
    return " ".join(plat.replace("-", " ").split())


def _meilleur_nom(mention: str, noms: list[str]) -> str | None:
    """Le nom de nœud le mieux ancré : l'égalité exacte prime, puis le plus
    court des noms contenant la mention, puis le plus long des noms contenus
    dans la mention (« Marc Dupont le voisin » → « Marc Dupont »)."""
    cible = _normaliser(mention)
    if not cible:
        return None
    contenants: list[str] = []
    contenus: list[str] = []
    for nom in noms:
        norme = _normaliser(nom)
        if norme == cible:
            return nom
        if cible in norme:
            contenants.append(nom)
        elif norme in cible:
            contenus.append(nom)
    if contenants:
        return min(contenants, key=len)
    if contenus:
        return max(contenus, key=len)
    return None


def resoudre(mentions: list[str], noms: list[str]) -> tuple[list[MentionResolue], list[str]]:
    """Chaque mention devient soit une `MentionResolue` (ancrée sur un vrai
    nom), soit une entrée de la liste des non-résolues — l'ordre d'origine est
    conservé dans les deux listes."""
    resolues: list[MentionResolue] = []
    non_resolues: list[str] = []
    for mention in mentions:
        nom = _meilleur_nom(mention, noms)
        if nom is None:
            non_resolues.append(mention)
        else:
            resolues.append(MentionResolue(mention=mention, noeud=nom))
    return resolues, non_resolues
