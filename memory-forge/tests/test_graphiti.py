"""Provenance réelle dans `GraphitiMemory` : la fonction pure de parsing, et
`search()` doublé (graphiti-core n'est pas installé en dev — extra séparé),
en instanciant `GraphitiMemory` sans passer par `__init__` (qui importe
graphiti-core)."""

from app.graph.graphiti import GraphitiMemory, _provenance_depuis_description


class TestProvenanceDepuisDescription:
    def test_une_description_document_donne_la_source_document(self):
        provenance = _provenance_depuis_description(
            "document:judo-club.md § Club de judo de Lyon"
        )

        assert provenance.source == "document"
        assert provenance.name == "judo-club.md § Club de judo de Lyon"

    def test_une_description_conversation_donne_la_source_conversation(self):
        provenance = _provenance_depuis_description("conversation:appel du lundi")

        assert provenance.source == "conversation"
        assert provenance.name == "appel du lundi"

    def test_une_source_inconnue_se_replie_sur_conversation(self):
        provenance = _provenance_depuis_description("podcast:épisode 3")

        assert provenance.source == "conversation"
        assert provenance.name == "épisode 3"

    def test_une_description_sans_separateur_se_replie_sur_conversation_et_garde_le_texte(self):
        provenance = _provenance_depuis_description("un texte sans deux-points")

        assert provenance.source == "conversation"
        assert provenance.name == "un texte sans deux-points"

    def test_aucune_description_se_replie_sur_conversation_inconnue(self):
        provenance = _provenance_depuis_description(None)

        assert provenance.source == "conversation"
        assert provenance.name == "inconnue"

    def test_une_description_vide_se_replie_sur_conversation_inconnue(self):
        provenance = _provenance_depuis_description("")

        assert provenance.source == "conversation"
        assert provenance.name == "inconnue"


class _FauxArete:
    """Reproduit la forme d'un `EntityEdge` renvoyé par `Graphiti.search()`, pour
    ce qui compte ici : `.fact`, `.episodes`, `.valid_at`, `.invalid_at`."""

    def __init__(self, fact, episodes=None, valid_at=None, invalid_at=None):
        self.fact = fact
        self.episodes = episodes or []
        self.valid_at = valid_at
        self.invalid_at = invalid_at


class _FauxDriver:
    """Reproduit `graphiti_core.driver.Neo4jDriver.execute_query` : une requête,
    des `records` accessibles par clé."""

    def __init__(self, descriptions_par_uuid):
        self._descriptions = descriptions_par_uuid
        self.nb_appels = 0
        self.dernier_uuids = None

    async def execute_query(self, _requete, **kwargs):
        self.nb_appels += 1
        uuids = kwargs["uuids"]
        self.dernier_uuids = uuids
        records = [
            {"uuid": uuid, "source_description": self._descriptions[uuid]}
            for uuid in uuids
            if uuid in self._descriptions
        ]
        return records, None, None


class _FauxGraphiti:
    def __init__(self, aretes, descriptions_par_uuid):
        self._aretes = aretes
        self.driver = _FauxDriver(descriptions_par_uuid)

    async def search(self, _query):
        return self._aretes


def _memoire_avec(aretes, descriptions_par_uuid):
    """Instancie `GraphitiMemory` sans passer par `__init__` (qui importe
    graphiti-core, absent en dev) et lui injecte un faux `_graphiti`."""
    memoire = GraphitiMemory.__new__(GraphitiMemory)
    memoire._graphiti = _FauxGraphiti(aretes, descriptions_par_uuid)
    return memoire


class _FauxGraphitiEnregistreur:
    """Capture les kwargs passés à `Graphiti.add_episode`."""

    def __init__(self):
        self.kwargs_add_episode = None

    async def add_episode(self, **kwargs):
        self.kwargs_add_episode = kwargs


def _stubber_graphiti_nodes(monkeypatch):
    """`GraphitiMemory.add_episode` importe `graphiti_core.nodes` (extra absent en
    dev) : on injecte un module factice avec un `EpisodeType` minimal."""
    import enum
    import sys
    import types

    class EpisodeType(enum.Enum):
        message = "message"
        text = "text"

    faux_nodes = types.ModuleType("graphiti_core.nodes")
    faux_nodes.EpisodeType = EpisodeType
    faux_graphiti_core = types.ModuleType("graphiti_core")
    faux_graphiti_core.nodes = faux_nodes
    monkeypatch.setitem(sys.modules, "graphiti_core", faux_graphiti_core)
    monkeypatch.setitem(sys.modules, "graphiti_core.nodes", faux_nodes)
    return EpisodeType


class TestAddEpisode:
    async def test_l_episode_part_avec_les_types_d_entites_du_domaine(self, monkeypatch):
        from app.graph.ontologie import TYPES_D_ENTITES
        from app.schemas import EpisodeIn

        _stubber_graphiti_nodes(monkeypatch)
        memoire = GraphitiMemory.__new__(GraphitiMemory)
        memoire._graphiti = _FauxGraphitiEnregistreur()

        await memoire.add_episode(
            EpisodeIn(content="Mon oncle Marcel commence la pétanque jeudi.",
                      source="conversation", name="marcel")
        )

        kwargs = memoire._graphiti.kwargs_add_episode
        assert kwargs is not None
        assert kwargs["entity_types"] is TYPES_D_ENTITES

    async def test_une_source_conversation_devient_un_episode_message(self, monkeypatch):
        from app.schemas import EpisodeIn

        episode_type = _stubber_graphiti_nodes(monkeypatch)
        memoire = GraphitiMemory.__new__(GraphitiMemory)
        memoire._graphiti = _FauxGraphitiEnregistreur()

        await memoire.add_episode(
            EpisodeIn(content="Bonjour.", source="conversation", name="salut")
        )

        assert memoire._graphiti.kwargs_add_episode["source"] is episode_type.message


class TestSearch:
    async def test_un_fait_issu_d_un_document_porte_la_provenance_document(self):
        memoire = _memoire_avec(
            aretes=[_FauxArete(fact="Le Judo a lieu mercredi.", episodes=["ep-1"])],
            descriptions_par_uuid={"ep-1": "document:judo-club.md § Horaires"},
        )

        facts = await memoire.search("judo")

        assert len(facts) == 1
        assert facts[0].text == "Le Judo a lieu mercredi."
        assert facts[0].provenance.source == "document"
        assert facts[0].provenance.name == "judo-club.md § Horaires"

    async def test_un_fait_issu_d_une_conversation_porte_la_provenance_conversation(self):
        memoire = _memoire_avec(
            aretes=[_FauxArete(fact="Léa fait du Judo.", episodes=["ep-2"])],
            descriptions_par_uuid={"ep-2": "conversation:appel du lundi"},
        )

        facts = await memoire.search("léa")

        assert facts[0].provenance.source == "conversation"
        assert facts[0].provenance.name == "appel du lundi"

    async def test_une_arete_sans_episode_se_replie_sur_conversation_inconnue(self):
        memoire = _memoire_avec(
            aretes=[_FauxArete(fact="Fait orphelin.", episodes=[])],
            descriptions_par_uuid={},
        )

        facts = await memoire.search("orphelin")

        assert facts[0].provenance.source == "conversation"
        assert facts[0].provenance.name == "inconnue"
        # Aucun uuid à résoudre : la requête Cypher ne doit pas partir.
        assert memoire._graphiti.driver.nb_appels == 0

    async def test_un_episode_introuvable_se_replie_sur_conversation_inconnue(self):
        memoire = _memoire_avec(
            aretes=[_FauxArete(fact="Fait mystère.", episodes=["ep-inconnu"])],
            descriptions_par_uuid={},
        )

        facts = await memoire.search("mystère")

        assert facts[0].provenance.source == "conversation"
        assert facts[0].provenance.name == "inconnue"

    async def test_zero_arete_ne_declenche_aucune_requete_cypher(self):
        memoire = _memoire_avec(aretes=[], descriptions_par_uuid={})

        facts = await memoire.search("rien")

        assert facts == []
        assert memoire._graphiti.driver.nb_appels == 0

    async def test_une_seule_requete_groupee_pour_plusieurs_faits(self):
        memoire = _memoire_avec(
            aretes=[
                _FauxArete(fact="Fait un.", episodes=["ep-1"]),
                _FauxArete(fact="Fait deux.", episodes=["ep-2"]),
            ],
            descriptions_par_uuid={
                "ep-1": "document:a.md",
                "ep-2": "conversation:b",
            },
        )

        facts = await memoire.search("peu importe")

        assert memoire._graphiti.driver.nb_appels == 1
        assert {f.provenance.source for f in facts} == {"document", "conversation"}
