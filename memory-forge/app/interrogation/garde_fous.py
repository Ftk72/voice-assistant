"""Garde-fous du repli Cypher libre (ticket wayfinder 0028) : rejet des clauses
d'écriture et `LIMIT` imposé — en pur texte, avant toute exécution. La session
Neo4j en lecture seule (executeur_neo4j) est la seconde ligne de défense."""

import re

LIMITE_PAR_DEFAUT = 100

# Mots-clés qui écrivent, détruisent ou sortent du périmètre lecture (CALL
# couvre les procédures apoc/db — aucun gabarit n'en a besoin).
_MOTS_INTERDITS = {
    "CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE",
    "DROP", "CALL", "LOAD", "FOREACH",
}


class RequeteInterdite(ValueError):
    """Le Cypher soumis contient une clause hors du périmètre lecture seule."""


def _sans_chaines(cypher: str) -> str:
    """Les littéraux entre quotes ne comptent pas : « Roset » contient SET."""
    return re.sub(r"'[^']*'|\"[^\"]*\"", " ", cypher)


def borner(cypher: str, limite: int = LIMITE_PAR_DEFAUT) -> str:
    """Le Cypher vérifié et borné, ou `RequeteInterdite`. Idempotent : un
    `LIMIT` déjà présent est conservé tel quel."""
    nu = _sans_chaines(cypher)
    if ";" in nu:
        raise RequeteInterdite("Une seule instruction Cypher à la fois (« ; » refusé).")
    mots = {mot.upper() for mot in re.findall(r"[A-Za-z_]+", nu)}
    interdits = sorted(mots & _MOTS_INTERDITS)
    if interdits:
        raise RequeteInterdite(
            f"Clause(s) hors lecture seule refusée(s) : {', '.join(interdits)}."
        )
    if "LIMIT" not in mots:
        return f"{cypher.rstrip()} LIMIT {limite}"
    return cypher
