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


TYPES_D_ENTITES: dict[str, type[BaseModel]] = {
    "Activite": Activite,
    "Personne": Personne,
    "Lieu": Lieu,
}
