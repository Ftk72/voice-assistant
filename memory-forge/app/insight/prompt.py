"""Construction des messages OpenAI-compat envoyés au LLM pour raconter la
mémoire (ticket wayfinder 0020) — fonction pure, testable sans réseau."""

from app.schemas import CondenseGraphe

_SYSTEME = (
    "Tu es la voix de la mémoire persistante d'un assistant vocal local. On te "
    "donne un condensé statistique du graphe mémoire (entités, faits, sujets "
    "dominants, entités qui font pont entre plusieurs sujets, et paires de "
    "sujets quasi pas reliées — des angles morts). Raconte en un seul "
    "paragraphe, en français, ce que cette mémoire sait — ton naturel, "
    "comme à l'oral, sans liste à puces, sans jamais inventer de chiffre ou de "
    "fait qui ne soit pas dans le condensé fourni."
)


def construire_messages(condense: CondenseGraphe) -> list[dict]:
    """Messages système + utilisateur (format OpenAI) injectant le condensé du
    graphe et demandant un unique paragraphe narratif, terminé au plus par une
    question sur un angle mort (ticket wayfinder 0021)."""
    lignes_sujets = (
        "\n".join(f"- {sujet.nom} ({sujet.taille} entités)" for sujet in condense.sujets)
        or "(aucun sujet distingué)"
    )
    ligne_ponts = ", ".join(condense.ponts) if condense.ponts else "(aucune entité-pont notable)"
    lignes_trous = (
        "\n".join(
            f"- « {trou.sujet_a} » et « {trou.sujet_b} » ({trou.nb_aretes} fait(s) entre eux)"
            for trou in condense.trous
        )
        or "(aucun angle mort notable)"
    )

    consigne_angle_mort = (
        " Termine ton paragraphe par au plus une question ouverte adressée à "
        "l'utilisateur, portant sur un seul de ces angles morts (par exemple : "
        "« … en revanche, j'ignore presque tout de ce qui relie X et Y — il y a "
        "peut-être quelque chose à me raconter là ? »)."
        if condense.trous
        else ""
    )

    utilisateur = (
        f"Statistiques du graphe mémoire :\n"
        f"- {condense.nb_entites} entités\n"
        f"- {condense.nb_faits} faits, dont {condense.nb_faits_obsoletes} obsolètes\n\n"
        f"Sujets dominants (triés par taille) :\n{lignes_sujets}\n\n"
        f"Entités qui font pont entre plusieurs sujets : {ligne_ponts}\n\n"
        f"Angles morts (paires de sujets quasi pas reliées) :\n{lignes_trous}\n\n"
        "Rédige un seul paragraphe en français qui raconte ce que sait cette "
        "mémoire, quels sont ses sujets dominants et quelles entités relient "
        "plusieurs sujets entre eux. Pas de liste à puces, pas de chiffre "
        "inventé — uniquement ceux fournis ci-dessus." + consigne_angle_mort
    )

    return [
        {"role": "system", "content": _SYSTEME},
        {"role": "user", "content": utilisateur},
    ]
