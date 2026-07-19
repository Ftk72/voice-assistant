"""Corpus synthétique de mémoire — ticket wayfinder 0016 (carte « graphe mémoire somptueux »).

Fabrique un graphe dense et déterministe couvrant les cas limites que la viz
doit savoir rendre : communautés de tailles contrastées, entités-ponts, trou
structurel, nœuds isolés, noms à rallonge accentués, faits obsolètes en masse,
deux provenances. La génération est pure (testée) ; l'écriture Neo4j (Cypher
direct sur le schéma que lisent `graphe_complet`/`neighborhood`) vit en bas de
ce module et se lance en CLI :

    uv run python -m scripts.corpus_synthetique            # purge + peuple
    uv run python -m scripts.corpus_synthetique --purger   # purge seulement

Le Cypher direct est un choix acté au ticket : l'ingestion normale
(POST /episodes → extraction LLM) est non déterministe et ne peut garantir la
topologie. Attention (impasse 2026-07-18) : l'index fulltext de Neo4j indexe
automatiquement toute nouvelle arête `RELATES_TO` — `/search` les voit donc
bel et bien, et Graphiti valide chaque enregistrement en pydantic : les champs
`group_id`/`created_at`/`name` (et leurs équivalents sur Entity/Episodic) sont
**obligatoires**, sous peine de 500 sur toute recherche. Les embeddings, eux,
restent absents (assumé : le corpus sort du fulltext, pas du vectoriel).
Chaque nœud porte `corpus: "synthetique"` : la purge ne touche jamais la
mémoire réelle.
"""

import argparse
import os
import random
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.graph.ontologie import TYPES_D_ENTITES

# --- Topologie voulue (les tests s'appuient sur ces constantes) ---

TAILLES_COMMUNAUTES = {
    "Travail": 110,  # la géante
    "Famille": 35,
    "Musique": 30,
    "Cuisine": 25,
    "Domotique": 22,
    "Voyages": 18,
    "Sport": 12,
    "Jeux de rôle": 3,  # la minuscule
}

# (nom du pont, communauté d'appartenance, communauté reliée) — « Léa relie
# Travail et Musique », l'exemple canonique de la carte.
PONTS = [
    ("Léa Fontaine", "Travail", "Musique"),
    ("Karim Bensaïd", "Famille", "Cuisine"),
    ("Chantal Robineau", "Domotique", "Travail"),
]

# Paire de communautés volontairement quasi déconnectée (au plus 1 arête) :
# le « trou structurel » que le ticket 0021 devra mettre en scène.
TROU_STRUCTUREL = ("Voyages", "Sport")

# Communauté minuscule rattachée au reste par UNE seule arête (vers Famille).
COMMUNAUTE_PERIPHERIQUE = "Jeux de rôle"

NOEUDS_ISOLES = [
    "Ticket de pressing",
    "Ampoule du garage",
    "Code du portail",
    "Carte de fidélité Biocoop",
    "Parapluie oublié",
    "Clé allen de 4",
]

NOMS_A_RALLONGE = [
    "Sophie-Charlotte de La Rochefoucauld-Montbéliard",
    "Église Saint-Jean-Baptiste-de-Belleville",
    "Étagère télescopique de l'entrée côté jardin",
]

# Toutes les arêtes de cette entité sont obsolètes — l'écho de l'expérience
# « déménagement » (la mémoire d'avant Lyon, invalidée en bloc).
ENTITE_TOUT_OBSOLETE = "Appartement de Lyon"

# Type déterministe des « choses » (ticket wayfinder 0029) : tout ce qui n'est
# pas explicitement listé ici est une personne (cf. `_type_de`). Choix par
# défaut pour ce qui ne colle précisément à aucun des 8 types : `Bien`.
TYPE_PAR_CHOSE: dict[str, str] = {
    # Travail
    "Projet Héliotrope": "Projet",
    "Réunion budget": "Bien",
    "Serveur de recette": "Bien",
    "Openspace du 3e": "Lieu",
    "Comité produit": "Organisation",
    "Sprint 42": "Projet",
    "Machine à café du couloir": "Bien",
    # Famille
    "Maison de Mamie Josette": "Lieu",
    "Repas du dimanche": "Bien",
    "Album photo 2019": "Bien",
    "Jardin partagé": "Lieu",
    ENTITE_TOUT_OBSOLETE: "Lieu",
    # Musique
    "Concert de jazz du Petit Duc": "Bien",
    "Guitare Takamine": "Bien",
    "Chorale du mardi": "Organisation",
    "Vinyle de Brassens": "Bien",
    "Studio de répétition": "Lieu",
    # Cuisine
    "Tajine aux abricots": "Aliment",
    "Robot pâtissier": "Bien",
    "Marché de la Plaine": "Lieu",
    "Levain maison": "Aliment",
    "Couteau santoku": "Bien",
    # Domotique
    "Capteur du salon": "Bien",
    "Passerelle Zigbee": "Bien",
    "Volet roulant est": "Bien",
    "Scénario réveil": "Bien",
    "Prise connectée du sapin": "Bien",
    # Voyages
    "Randonnée des Écrins": "Bien",
    "Vol pour Lisbonne": "Bien",
    "Auberge de Porto": "Lieu",
    "Sac de 40 litres": "Bien",
    "Carnet de voyage": "Bien",
    # Sport
    "Semi-marathon de Marseille": "Bien",
    "Club d'escalade": "Organisation",
    "Vélo gravel": "Bien",
    "Séance du jeudi": "Bien",
    # Jeux de rôle
    "Campagne de l'Œil noir": "Projet",
    "Dés fétiches": "Bien",
    "Écran du maître de jeu": "Bien",
    # Isolés
    "Ticket de pressing": "Bien",
    "Ampoule du garage": "Bien",
    "Code du portail": "Bien",
    "Carte de fidélité Biocoop": "Bien",
    "Parapluie oublié": "Bien",
    "Clé allen de 4": "Bien",
    # Noms à rallonge
    "Sophie-Charlotte de La Rochefoucauld-Montbéliard": "Personne",
    "Église Saint-Jean-Baptiste-de-Belleville": "Lieu",
    "Étagère télescopique de l'entrée côté jardin": "Bien",
}


def _type_de(nom: str) -> str:
    """Type déterministe d'une entité du corpus : les « choses » suivent
    `TYPE_PAR_CHOSE`, tout le reste (personnes du paquet, ponts) est `Personne`."""
    return TYPE_PAR_CHOSE.get(nom, "Personne")


# --- Cas fautifs volontaires (ticket wayfinder 0029) : matière à corriger
# depuis /viz — jamais introduits dans la topologie normale (communautés,
# ponts, trou structurel), pour ne perturber aucun test existant. ---
CAS_FAUTIFS = {
    # Entité mal orthographiée : nouvelle entité dédiée, jamais une existante.
    "entite_mal_orthographiee": "Aurlie Ferrand",
    # Entité au mauvais type : un animal volontairement typé Personne (reçoit
    # `Personne` par défaut via `_type_de`, faute assumée — ne pas ajouter
    # d'entrée `Animal` dans TYPE_PAR_CHOSE pour ce nom).
    "entite_mauvais_type": "Rex",
    # Fait faux : arête dédiée, contenu manifestement faux.
    "fait_faux_source": "Aurlie Ferrand",
    "fait_faux_cible": "Rex",
    "fait_faux_texte": (
        "Aurlie Ferrand a piloté un avion de chasse en solo à 8 ans, "
        "avec Rex comme copilote"
    ),
}

PRENOMS = [
    "Léa", "Karim", "Chantal", "Marc", "Aïcha", "Benoît", "Cécile", "David",
    "Élodie", "Fabrice", "Gaëlle", "Hugo", "Inès", "Julien", "Khadija",
    "Laurent", "Maëlys", "Nicolas", "Océane", "Pierre", "Quitterie", "Rémi",
    "Salomé", "Thibault", "Ursule", "Valérie", "Wassim", "Xavière", "Yanis", "Zoé",
]
NOMS_DE_FAMILLE = [
    "Fontaine", "Bensaïd", "Robineau", "Lefèvre", "Marchand", "Nguyen",
    "Perrault", "Sánchez", "Texier", "Vasseur", "Weiss", "Zimmermann",
    "Delacroix", "Ferrand", "Girard", "Hébert",
]

CHOSES_PAR_COMMUNAUTE = {
    "Travail": ["Projet Héliotrope", "Réunion budget", "Serveur de recette",
                "Openspace du 3e", "Comité produit", "Sprint 42", "Machine à café du couloir"],
    "Famille": ["Maison de Mamie Josette", "Repas du dimanche", "Album photo 2019",
                "Jardin partagé", ENTITE_TOUT_OBSOLETE],
    "Musique": ["Concert de jazz du Petit Duc", "Guitare Takamine", "Chorale du mardi",
                "Vinyle de Brassens", "Studio de répétition"],
    "Cuisine": ["Tajine aux abricots", "Robot pâtissier", "Marché de la Plaine",
                "Levain maison", "Couteau santoku"],
    "Domotique": ["Capteur du salon", "Passerelle Zigbee", "Volet roulant est",
                  "Scénario réveil", "Prise connectée du sapin"],
    "Voyages": ["Randonnée des Écrins", "Vol pour Lisbonne", "Auberge de Porto",
                "Sac de 40 litres", "Carnet de voyage"],
    "Sport": ["Semi-marathon de Marseille", "Club d'escalade", "Vélo gravel",
              "Séance du jeudi"],
    "Jeux de rôle": ["Campagne de l'Œil noir", "Dés fétiches", "Écran du maître de jeu"],
}

GABARITS_DE_FAITS = [
    "{a} est étroitement lié à {b}",
    "{a} a été mentionné en même temps que {b}",
    "{a} dépend de {b} d'après une conversation récente",
    "{a} et {b} reviennent souvent ensemble dans les échanges",
    "{a} a organisé quelque chose avec {b}",
]

EPISODES_CONVERSATION = [
    "conversation du 3 mars 2026", "conversation du 14 avril 2026",
    "conversation du 2 mai 2026", "conversation du 27 mai 2026",
    "conversation du 11 juin 2026", "conversation du 8 juillet 2026",
]
EPISODES_DOCUMENT = [
    "notes-domotique.md", "recette-tajine.pdf", "carnet-voyage-2025.md",
    "compte-rendu-sprint42.md", "programme-chorale.pdf",
]

DEBUT_DES_TEMPS = datetime(2024, 7, 1, tzinfo=UTC)


@dataclass(frozen=True)
class Arete:
    source: str
    target: str
    fait: str
    provenance_source: str  # « conversation » | « document »
    provenance_nom: str
    valide_depuis: datetime
    obsolete_depuis: datetime | None


@dataclass
class Corpus:
    """Le graphe synthétique complet, prêt à écrire — `communaute_de` garde la
    vérité terrain (utile aux tests et, plus tard, pour juger Louvain)."""

    communaute_de: dict[str, str] = field(default_factory=dict)
    noeuds_isoles: list[str] = field(default_factory=list)
    aretes: list[Arete] = field(default_factory=list)

    @property
    def noeuds(self) -> list[str]:
        return [*self.communaute_de, *self.noeuds_isoles]


def _paquet_de_personnes(rng: random.Random) -> list[str]:
    """Un paquet global, distribué sans remise : un nom n'appartient qu'à une
    communauté (le tirage par communauté créait des doublons inter-communautés).
    Les ponts en sont retirés — ils sont placés explicitement."""
    reserves = {pont for pont, _, _ in PONTS}
    personnes = [
        f"{p} {n}" for p in PRENOMS for n in NOMS_DE_FAMILLE if f"{p} {n}" not in reserves
    ]
    rng.shuffle(personnes)
    return personnes


def _noms_de_communaute(nom: str, taille: int, paquet: list[str]) -> list[str]:
    """Des noms plausibles : les choses thématiques d'abord, puis des personnes
    dépilées du paquet global."""
    noms = list(CHOSES_PAR_COMMUNAUTE[nom])
    while len(noms) < taille:
        noms.append(paquet.pop())
    return noms[:taille]


def _dates(rng: random.Random, obsolete: bool) -> tuple[datetime, datetime | None]:
    valide = DEBUT_DES_TEMPS + timedelta(days=rng.randint(0, 700), hours=rng.randint(0, 23))
    if not obsolete:
        return valide, None
    return valide, valide + timedelta(days=rng.randint(7, 300))


def _fait(a: str, b: str, rng: random.Random) -> str:
    return rng.choice(GABARITS_DE_FAITS).format(a=a, b=b)


class _Fabrique:
    """Assemble les arêtes en garantissant l'unicité des paires."""

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.aretes: list[Arete] = []
        self._paires: set[frozenset[str]] = set()

    def relier(self, a: str, b: str, provenance_forcee: str | None = None) -> None:
        paire = frozenset((a, b))
        if a == b or paire in self._paires:
            return
        self._paires.add(paire)
        obsolete = self.rng.random() < 0.15
        valide, invalide = _dates(self.rng, obsolete)
        source_prov = provenance_forcee or (
            "document" if self.rng.random() < 0.3 else "conversation"
        )
        nom_prov = self.rng.choice(
            EPISODES_DOCUMENT if source_prov == "document" else EPISODES_CONVERSATION
        )
        self.aretes.append(
            Arete(a, b, _fait(a, b, self.rng), source_prov, nom_prov, valide, invalide)
        )


def generer_corpus(graine: int = 42) -> Corpus:
    rng = random.Random(graine)
    corpus = Corpus(noeuds_isoles=list(NOEUDS_ISOLES))
    fabrique = _Fabrique(rng)

    paquet = _paquet_de_personnes(rng)
    membres: dict[str, list[str]] = {}
    for communaute, taille in TAILLES_COMMUNAUTES.items():
        noms = _noms_de_communaute(communaute, taille, paquet)
        membres[communaute] = noms
        for nom in noms:
            corpus.communaute_de[nom] = communaute

    # Les ponts appartiennent à leur communauté d'origine (remplacent un membre).
    for pont, origine, _ in PONTS:
        remplace = membres[origine][-1]
        membres[origine][-1] = pont
        del corpus.communaute_de[remplace]
        corpus.communaute_de[pont] = origine

    # Trois noms à rallonge, greffés sur les trois plus grosses communautés.
    for nom, communaute in zip(NOMS_A_RALLONGE, list(TAILLES_COMMUNAUTES)[:3], strict=False):
        membres[communaute].append(nom)
        corpus.communaute_de[nom] = communaute

    # Intra-communauté : attachement préférentiel (des hubs émergent), plus
    # quelques arêtes aléatoires pour densifier.
    for noms in membres.values():
        cibles: list[str] = [noms[0]]
        for nom in noms[1:]:
            for cible in {rng.choice(cibles) for _ in range(2)}:
                fabrique.relier(nom, cible)
                cibles.append(cible)
            cibles.append(nom)
        for _ in range(len(noms) // 3):
            fabrique.relier(rng.choice(noms), rng.choice(noms))

    # Ponts : 4 arêtes chacun vers la communauté d'en face.
    for pont, _, cible in PONTS:
        for autre in rng.sample(membres[cible], k=4):
            fabrique.relier(pont, autre)

    # Connexité : chaque communauté se rattache à la géante par 2 arêtes —
    # sauf la périphérique (1 seule arête, vers Famille) et en respectant le
    # trou structurel (aucune arête directe Voyages↔Sport).
    geante = next(iter(TAILLES_COMMUNAUTES))
    for communaute, noms in membres.items():
        if communaute == geante:
            continue
        if communaute == COMMUNAUTE_PERIPHERIQUE:
            fabrique.relier(rng.choice(noms), rng.choice(membres["Famille"]))
            continue
        for _ in range(2):
            fabrique.relier(rng.choice(noms), rng.choice(membres[geante]))

    # L'entité tout-obsolète : ses faits basculent tous en obsolescence.
    fabrique.aretes = [
        Arete(
            a.source, a.target, a.fait, a.provenance_source, a.provenance_nom,
            a.valide_depuis,
            a.obsolete_depuis
            or (a.valide_depuis + timedelta(days=30)
                if ENTITE_TOUT_OBSOLETE in (a.source, a.target) else None),
        )
        for a in fabrique.aretes
    ]

    # Cas fautifs volontaires (ticket wayfinder 0029) : matière à corriger
    # depuis /viz, en dehors de la topologie testée ci-dessus.
    corpus.noeuds_isoles.append(CAS_FAUTIFS["entite_mal_orthographiee"])
    corpus.noeuds_isoles.append(CAS_FAUTIFS["entite_mauvais_type"])
    fabrique.aretes.append(
        Arete(
            CAS_FAUTIFS["fait_faux_source"],
            CAS_FAUTIFS["fait_faux_cible"],
            CAS_FAUTIFS["fait_faux_texte"],
            "conversation",
            EPISODES_CONVERSATION[0],
            DEBUT_DES_TEMPS,
            None,
        )
    )

    corpus.aretes = fabrique.aretes
    return corpus


# --- Écriture Neo4j (Cypher direct, schéma lu par graphe_complet/neighborhood) ---


def _uuid(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128)))


# Champs exigés par les modèles pydantic de Graphiti (EntityNode, EntityEdge,
# EpisodicNode) : sans eux, toute recherche fulltext qui croise le corpus rend
# un 500 (impasse 2026-07-18). Valeurs alignées sur la mémoire réelle
# (group_id vide = graphe unique) et déterministes (corpus rejouable).
_GROUP_ID = ""
_CREATED_AT = datetime(2026, 1, 1, tzinfo=UTC)
_SOURCE_EPISODE = {"conversation": "message", "document": "text"}


def preparer_lignes(corpus: Corpus) -> tuple[list[dict], list[dict], list[dict]]:
    """Prépare (épisodes, nœuds, arêtes) prêts pour l'UNWIND Cypher — fonction
    pure et déterministe, testée : chaque ligne porte les champs que Graphiti
    valide en pydantic au moment d'une recherche."""
    rng = random.Random(0)
    episodes = {
        (a.provenance_source, a.provenance_nom) for a in corpus.aretes
    }
    lignes_episodes = [
        {"uuid": _uuid(rng), "source": _SOURCE_EPISODE[source], "nom": nom,
         "description": f"{source}:{nom}", "contenu": f"Corpus synthétique — {source} {nom}.",
         "group_id": _GROUP_ID, "cree": _CREATED_AT, "valide": _CREATED_AT}
        for source, nom in sorted(episodes)
    ]
    uuid_episode = {
        (e["description"].split(":")[0], e["nom"]): e["uuid"] for e in lignes_episodes
    }
    lignes_noeuds = [
        {"nom": nom, "uuid": _uuid(rng), "group_id": _GROUP_ID, "cree": _CREATED_AT,
         "resume": "", "type": _type_de(nom)}
        for nom in corpus.noeuds
    ]
    lignes_aretes = [
        {
            "source": a.source, "target": a.target, "uuid": _uuid(rng),
            "fait": a.fait, "valide": a.valide_depuis,
            "invalide": a.obsolete_depuis,
            "episodes": [uuid_episode[(a.provenance_source, a.provenance_nom)]],
            "group_id": _GROUP_ID, "cree": _CREATED_AT, "nom": "RELIE",
        }
        for a in corpus.aretes
    ]
    return lignes_episodes, lignes_noeuds, lignes_aretes


def peupler(corpus: Corpus, uri: str, utilisateur: str, mot_de_passe: str) -> dict[str, int]:
    """Purge l'ancien corpus synthétique puis écrit le nouveau. Idempotent."""
    from neo4j import GraphDatabase

    lignes_episodes, lignes_noeuds, lignes_aretes = preparer_lignes(corpus)

    lignes_par_type: dict[str, list[dict]] = {}
    for ligne in lignes_noeuds:
        if ligne["type"] not in TYPES_D_ENTITES:
            raise ValueError(f"type hors liste blanche : {ligne['type']!r}")
        lignes_par_type.setdefault(ligne["type"], []).append(ligne)

    with GraphDatabase.driver(uri, auth=(utilisateur, mot_de_passe)) as driver:
        purger(driver)
        driver.execute_query(
            """
            UNWIND $lignes AS l
            CREATE (:Episodic {uuid: l.uuid, name: l.nom,
                               source: l.source,
                               source_description: l.description,
                               content: l.contenu,
                               group_id: l.group_id,
                               created_at: l.cree, valid_at: l.valide,
                               entity_edges: [],
                               corpus: 'synthetique'})
            """,
            lignes=lignes_episodes,
        )
        for type_, lignes in lignes_par_type.items():
            # Whitelist déjà vérifiée ci-dessus : seul cas où un label Cypher
            # est interpolé directement (les labels ne sont pas paramétrables).
            driver.execute_query(
                f"""
                UNWIND $lignes AS l
                CREATE (:Entity:{type_} {{uuid: l.uuid, name: l.nom,
                                 group_id: l.group_id, created_at: l.cree,
                                 summary: l.resume, labels: ['Entity', l.type],
                                 corpus: 'synthetique'}})
                """,
                lignes=lignes,
            )
        driver.execute_query(
            """
            UNWIND $lignes AS l
            MATCH (a:Entity {name: l.source, corpus: 'synthetique'})
            MATCH (b:Entity {name: l.target, corpus: 'synthetique'})
            CREATE (a)-[:RELATES_TO {uuid: l.uuid, name: l.nom, fact: l.fait,
                                     valid_at: l.valide, invalid_at: l.invalide,
                                     episodes: l.episodes,
                                     group_id: l.group_id, created_at: l.cree,
                                     corpus: 'synthetique'}]->(b)
            """,
            lignes=lignes_aretes,
        )
    return {
        "episodes": len(lignes_episodes),
        "noeuds": len(lignes_noeuds),
        "aretes": len(lignes_aretes),
    }


def purger(driver) -> int:
    """Supprime tout le corpus synthétique — la mémoire réelle est intacte."""
    records, _, _ = driver.execute_query(
        "MATCH (n {corpus: 'synthetique'}) DETACH DELETE n RETURN count(n) AS n"
    )
    return records[0]["n"]


def main() -> None:
    parseur = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parseur.add_argument("--uri", default="bolt://localhost:7687")
    parseur.add_argument("--utilisateur", default="neo4j")
    parseur.add_argument("--graine", type=int, default=42)
    parseur.add_argument("--purger", action="store_true",
                         help="purge le corpus synthétique sans le recréer")
    options = parseur.parse_args()
    mot_de_passe = os.environ.get("NEO4J_PASSWORD") or os.environ.get(
        "MEMORY_FORGE_NEO4J_PASSWORD"
    )
    if not mot_de_passe:
        raise SystemExit("Définir NEO4J_PASSWORD (cf. .env à la racine du dépôt).")

    if options.purger:
        from neo4j import GraphDatabase

        with GraphDatabase.driver(
            options.uri, auth=(options.utilisateur, mot_de_passe)
        ) as driver:
            print(f"Corpus synthétique purgé : {purger(driver)} nœud(s).")
        return

    corpus = generer_corpus(options.graine)
    bilan = peupler(corpus, options.uri, options.utilisateur, mot_de_passe)
    print(
        f"Corpus synthétique en place : {bilan['noeuds']} entités, "
        f"{bilan['aretes']} faits, {bilan['episodes']} épisodes."
    )


if __name__ == "__main__":
    main()
