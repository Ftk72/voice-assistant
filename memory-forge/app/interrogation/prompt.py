"""Les deux prompts du canal d'interrogation (ticket wayfinder 0028) :
l'aiguillage structuré (un seul appel, JSON strict) et la formulation de la
réponse depuis les résultats vérité-terrain — le LLM n'a jamais le droit de
répondre de sa propre tête."""

import json

from app.schemas import ContexteInterrogation

_SYSTEME_AIGUILLAGE = """\
Tu traduis une question française sur un graphe de mémoire en une requête.
Tu réponds UNIQUEMENT par un objet JSON, sans autre texte.

Gabarits disponibles (préférés au Cypher libre) :
- "faits_sur" — que sait-on d'une entité ; paramètres : {"entite": "<nom>"}
- "lien_entre" — le lien entre deux entités (arête directe sinon plus court
  chemin) ; paramètres : {"entite_a": "<nom>", "entite_b": "<nom>"}
- "lecture_temporelle" — l'histoire d'une entité dans le temps (depuis quand,
  jusqu'à quand) ; paramètres : {"entite": "<nom>"}
- "autour_du_sujet" — tout ce qui touche à un thème ; paramètres :
  {"sujet": "<mot ou expression>"}
- "compter" — combien de faits/entités, éventuellement sur un thème ;
  paramètres : {"sujet": "<thème>"} ou {"sujet": null}

Forme de la réponse :
{"mentions": ["<entités citées dans la question>"],
 "gabarit": "<nom du gabarit>", "parametres": {…}}
ou, si aucun gabarit ne colle, un Cypher LECTURE SEULE sur le schéma
(n:Entity {name})-[r:RELATES_TO {fact, valid_at, invalid_at}]-(m:Entity) :
{"mentions": […], "cypher": "MATCH … RETURN … LIMIT 50"}

"mentions" liste les entités nommées telles que la question les cite : le
serveur les résout lui-même contre les vrais nœuds, n'invente jamais de nom."""

_SYSTEME_FORMULATION = """\
Tu réponds en français à une question sur la mémoire de l'assistant.
Règle absolue : ta réponse s'appuie EXCLUSIVEMENT sur les résultats fournis
(vérité-terrain issue du graphe) — rien de ta propre connaissance, aucun fait
inventé. Réponse orale, un paragraphe court, sans liste ni markdown."""


def construire_messages_aiguillage(
    question: str, contexte: ContexteInterrogation | None
) -> list[dict[str, str]]:
    corps = f"Question : {question}"
    if contexte and (contexte.question_precedente or contexte.entites):
        corps += (
            f"\nContexte (échange précédent) : question « {contexte.question_precedente or ''} », "
            f"entités déjà résolues : {', '.join(contexte.entites) or 'aucune'}."
        )
    return [
        {"role": "system", "content": _SYSTEME_AIGUILLAGE},
        {"role": "user", "content": corps},
    ]


def construire_messages_formulation(question: str, resultats: list[dict]) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": _SYSTEME_FORMULATION},
        {
            "role": "user",
            "content": (
                f"Question : {question}\n"
                f"Résultats du graphe ({len(resultats)} ligne(s)) :\n"
                f"{json.dumps(resultats, ensure_ascii=False, indent=2)}"
            ),
        },
    ]
