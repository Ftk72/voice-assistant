"""Les cinq gabarits Cypher écrits main (ticket wayfinder 0028), sur le schéma
Graphiti réel (`Entity.name`, `RELATES_TO {fact, valid_at, invalid_at}` — cf.
app/graph/graphiti.py). `parametres_entites` déclare les paramètres qui doivent
être des noms de nœuds résolus : sans résolution, la requête ne part pas."""

from dataclasses import dataclass, field

from app.schemas import RequeteCypher


@dataclass(frozen=True)
class Gabarit:
    nom: str
    cypher: str
    parametres: tuple[str, ...]
    parametres_entites: frozenset[str] = field(default_factory=frozenset)


GABARITS: dict[str, Gabarit] = {
    gabarit.nom: gabarit
    for gabarit in (
        Gabarit(
            nom="faits_sur",
            cypher="""
MATCH (a:Entity {name: $entite})-[r:RELATES_TO]-(b:Entity)
RETURN a.name AS source, r.fact AS fait, b.name AS cible,
       r.valid_at AS valide_depuis, r.invalid_at AS obsolete_depuis
LIMIT 50""".strip(),
            parametres=("entite",),
            parametres_entites=frozenset({"entite"}),
        ),
        Gabarit(
            nom="lien_entre",
            cypher="""
MATCH (a:Entity {name: $entite_a}), (b:Entity {name: $entite_b})
OPTIONAL MATCH (a)-[direct:RELATES_TO]-(b)
OPTIONAL MATCH chemin = shortestPath((a)-[:RELATES_TO*..6]-(b))
RETURN a.name AS source, b.name AS cible,
       collect(DISTINCT direct.fact) AS faits_directs,
       [n IN nodes(chemin) | n.name] AS chemin,
       [r IN relationships(chemin) | r.fact] AS faits_du_chemin
LIMIT 25""".strip(),
            parametres=("entite_a", "entite_b"),
            parametres_entites=frozenset({"entite_a", "entite_b"}),
        ),
        Gabarit(
            nom="lecture_temporelle",
            cypher="""
MATCH (a:Entity {name: $entite})-[r:RELATES_TO]-(b:Entity)
RETURN r.fact AS fait, b.name AS cible,
       r.valid_at AS valide_depuis, r.invalid_at AS obsolete_depuis
ORDER BY r.valid_at
LIMIT 50""".strip(),
            parametres=("entite",),
            parametres_entites=frozenset({"entite"}),
        ),
        Gabarit(
            nom="autour_du_sujet",
            cypher="""
MATCH (a:Entity)-[r:RELATES_TO]-(b:Entity)
WHERE toLower(r.fact) CONTAINS toLower($sujet)
   OR toLower(a.name) CONTAINS toLower($sujet)
RETURN a.name AS source, r.fact AS fait, b.name AS cible
LIMIT 50""".strip(),
            parametres=("sujet",),
        ),
        Gabarit(
            nom="compter",
            cypher="""
MATCH (a:Entity)-[r:RELATES_TO]-(b:Entity)
WHERE $sujet IS NULL OR toLower(r.fact) CONTAINS toLower($sujet)
RETURN count(DISTINCT r) AS nb_faits, count(DISTINCT a) AS nb_entites
LIMIT 1""".strip(),
            parametres=("sujet",),
        ),
    )
}


def construire_requete(nom: str, parametres: dict[str, str | None]) -> RequeteCypher:
    """La requête prête à exécuter : seuls les paramètres déclarés du gabarit
    passent (le reste est ignoré), les absents valent None."""
    gabarit = GABARITS[nom]
    return RequeteCypher(
        cypher=gabarit.cypher,
        parametres={p: parametres.get(p) for p in gabarit.parametres},
    )
