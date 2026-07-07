"""Ontologie des types d'entités passés à `Graphiti.add_episode(entity_types=…)`.

Pourquoi (diagnostic du 2026-07-06) : sans type explicite, le prompt d'extraction de
nœuds de graphiti-core exclut les « generic event/activity nouns » et le 35B applique
cette règle de façon instable aux activités nues (« judo », « pétanque ») — l'activité,
seul second nœud possible d'un épisode court, saute, donc zéro arête, donc zéro fait
(0/5 constaté). Déclarer un type `Activite` déplace ce jugement flou « générique vs
spécifique » vers une classification par type, plus stable.

Contraintes de graphiti-core 0.29.2 :
- format : dict nom → modèle pydantic ; la description montrée au LLM est la
  **docstring** du modèle (`_build_entity_types_context`, node_operations.py) ;
- aucun champ ne doit redéfinir ceux d'`EntityNode` (uuid, name, group_id, labels,
  created_at, name_embedding, summary, attributes) — d'où des modèles sans champ ;
- le nom du type devient un label Neo4j : ASCII, sans espace ni accent.

Module pur pydantic : importable sans l'extra graphiti (les tests en dépendent).
"""

from pydantic import BaseModel


class Activite(BaseModel):
    """Une activité pratiquée ou suivie par quelqu'un : sport (judo, pétanque,
    natation, vélo…), loisir (peinture, échecs, jardinage…), cours ou activité
    récurrente (cours de piano, club de lecture…). Extraire l'activité même
    nommée seule, sans qualificatif : « judo » et « pétanque » sont des
    activités valides."""


class Personne(BaseModel):
    """Une personne : prénom, nom complet, ou terme de parenté qualifié par son
    possesseur (« la fille de Léa », « l'oncle Marcel »)."""


class Lieu(BaseModel):
    """Un lieu : ville, pays, adresse, ou endroit nommé (gymnase, club, école,
    parc…)."""


class Organisation(BaseModel):
    """Un collectif nommé auquel la personne appartient ou qu'elle fréquente
    régulièrement : employeur, école, club, équipe, association (« Ubisoft »,
    « le JC Lyon », « l'école de ma fille »). Distinct d'un Lieu : c'est le
    groupe humain, pas le bâtiment ni la ville."""


class Animal(BaseModel):
    """Un animal de compagnie appartenant à quelqu'un ou lié à lui, nommé
    (« Rex », « Minou ») ou désigné par son espèce (« mon chat »)."""


class Bien(BaseModel):
    """Une possession durable, individuelle et identifiable, dont on parle
    comme d'une chose précise et unique : véhicule (« ma Clio »), logement
    (« mon appartement »), instrument (« ma guitare »), matériel notable
    (« mon vélo », « mon ordinateur »). PAS un consommable ni un objet
    générique du quotidien (courses, vêtements, nourriture) : le test est
    « existera-t-elle encore et comptera-t-elle dans un an ? »."""


class Projet(BaseModel):
    """Une entreprise ou un objectif que la personne poursuit dans la durée,
    SANS échéance datée : apprendre une langue, écrire un livre, construire
    quelque chose, un but de carrière (« j'apprends l'espagnol », « mon
    assistant vocal »). PAS une tâche ponctuelle à faire pour une date
    (« appeler le plombier mardi ») — ça, c'est l'agenda."""


class Aliment(BaseModel):
    """Un aliment, boisson ou ingrédient, cible d'un goût, d'une aversion ou
    d'une allergie (« les noix », « le café serré », « les fruits de mer »).
    Couvre la zone la plus fréquente et la plus sensible des préférences
    (allergie alimentaire comprise)."""


TYPES_D_ENTITES: dict[str, type[BaseModel]] = {
    "Activite": Activite,
    "Personne": Personne,
    "Lieu": Lieu,
    "Organisation": Organisation,
    "Animal": Animal,
    "Bien": Bien,
    "Projet": Projet,
    "Aliment": Aliment,
}
