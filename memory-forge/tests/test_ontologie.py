"""Ontologie des types d'entités passés à Graphiti : des modèles pydantic sans champ
(la description vient de la docstring), importables sans l'extra graphiti.

Contexte (diagnostic 2026-07-06) : sans type explicite, le 35B tranche de façon
instable « générique vs spécifique » pour les activités nues (« judo », « pétanque »)
et rate le second nœud — donc zéro fait sur un épisode court. Le type `Activite`
déplace ce jugement flou vers une classification par type."""

from app.graph.ontologie import TYPES_D_ENTITES

# Champs de graphiti_core.nodes.EntityNode (0.29.2) : un type d'entité qui redéfinit
# l'un d'eux est rejeté par validate_entity_types au premier add_episode.
CHAMPS_RESERVES_ENTITY_NODE = {
    "uuid",
    "name",
    "group_id",
    "labels",
    "created_at",
    "name_embedding",
    "summary",
    "attributes",
}


class TestTypesDEntites:
    def test_le_type_activite_est_declare(self):
        assert "Activite" in TYPES_D_ENTITES

    def test_la_description_d_activite_nomme_les_sports_et_loisirs(self):
        description = TYPES_D_ENTITES["Activite"].__doc__

        assert "judo" in description
        assert "pétanque" in description
        assert "natation" in description

    def test_les_huit_types_de_l_adr_0011_sont_declares(self):
        # ADR 0011 : le trio initial + cinq types de nœuds durables.
        attendus = {
            "Personne",
            "Lieu",
            "Activite",
            "Organisation",
            "Animal",
            "Bien",
            "Projet",
            "Aliment",
        }
        assert attendus <= set(TYPES_D_ENTITES)

    def test_organisation_est_distincte_d_un_lieu(self):
        # ADR 0011 : le collectif humain, pas le bâtiment ni la ville.
        description = TYPES_D_ENTITES["Organisation"].__doc__

        assert "employeur" in description
        assert "Lieu" in description

    def test_animal_couvre_les_animaux_de_compagnie(self):
        assert "compagnie" in TYPES_D_ENTITES["Animal"].__doc__

    def test_bien_est_borne_par_le_test_de_duree(self):
        # ADR 0011 : « encore là et important dans un an ? », pas les consommables.
        description = TYPES_D_ENTITES["Bien"].__doc__

        assert "an" in description
        assert "consommable" in description

    def test_projet_se_distingue_de_la_tache_d_agenda(self):
        # ADR 0011 : projet durable = sans échéance datée (sinon, c'est l'agenda).
        description = TYPES_D_ENTITES["Projet"].__doc__

        assert "échéance" in description
        assert "agenda" in description

    def test_aliment_couvre_les_allergies(self):
        # ADR 0011 : zone la plus fréquente et la plus sensible.
        assert "allergie" in TYPES_D_ENTITES["Aliment"].__doc__

    def test_chaque_type_a_une_description_francaise_non_vide(self):
        for nom, modele in TYPES_D_ENTITES.items():
            assert modele.__doc__ and modele.__doc__.strip(), f"{nom} sans description"

    def test_aucun_type_ne_redefinit_un_champ_reserve_d_entity_node(self):
        for nom, modele in TYPES_D_ENTITES.items():
            collisions = set(modele.model_fields) & CHAMPS_RESERVES_ENTITY_NODE
            assert not collisions, f"{nom} redéfinit {collisions}"

    def test_les_noms_de_types_sont_des_labels_neo4j_surs(self):
        """Le nom du type devient un label Neo4j : ASCII sans espace ni accent."""
        for nom in TYPES_D_ENTITES:
            assert nom.isidentifier() and nom.isascii(), f"{nom} n'est pas un label sûr"
