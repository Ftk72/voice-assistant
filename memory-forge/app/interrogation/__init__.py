"""Interroger la mémoire sans halluciner (ticket wayfinder 0028, modèle
LinkQ) : la logique de service partagée entre la route `POST /interroger` et
l'outil MCP `interroger_memoire`. Le LLM ne fait que traduire (aiguillage) et
formuler ; la résolution d'entités, les garde-fous et l'exécution restent
déterministes côté serveur."""

from app.graph.base import GraphMemory
from app.interrogation.base import TraducteurQuestion
from app.interrogation.executeur import ExecuteurCypher
from app.interrogation.gabarits import GABARITS, construire_requete
from app.interrogation.garde_fous import borner
from app.interrogation.resolution import resoudre
from app.schemas import (
    Aiguillage,
    ContexteInterrogation,
    EtatVue,
    InterrogationIn,
    InterrogationReponse,
    MentionResolue,
    Monologue,
    RequeteCypher,
)

# Même plafond que l'API /graph/complet : la liste des noms sert d'ancre de
# résolution et de filtre du surlignage.
LIMITE_NOMS = 5000

REPONSE_SANS_RESULTAT = "Je n'ai rien trouvé dans le graphe à ce sujet."


def _construire_vue(resultats: list[dict], noms: list[str], resolus: list[str]) -> EtatVue:
    """Les nœuds à surligner : les entités résolues puis toute valeur des
    résultats qui est un vrai nom de nœud — jamais un nom inventé. Le focus
    (vol de caméra) est le premier surligné."""
    connus = set(noms)
    surligner: list[str] = []

    def retenir(valeur) -> None:
        if isinstance(valeur, str) and valeur in connus and valeur not in surligner:
            surligner.append(valeur)
        elif isinstance(valeur, list):
            for v in valeur:
                retenir(v)

    for nom in resolus:
        retenir(nom)
    for ligne in resultats:
        for valeur in ligne.values():
            retenir(valeur)
    return EtatVue(surligner=surligner, focus=surligner[0] if surligner else None)


def _requete_depuis_aiguillage(
    aiguillage: Aiguillage, table: dict[str, str]
) -> tuple[RequeteCypher | None, str | None]:
    """La requête exécutable, ou (None, raison) si l'aiguillage ne le permet
    pas — paramètre-entité non résolu, gabarit inconnu du LLM…"""
    if aiguillage.cypher:
        return RequeteCypher(cypher=borner(aiguillage.cypher)), None
    if not aiguillage.gabarit:
        return None, "le LLM n'a rendu ni gabarit ni requête"
    gabarit = GABARITS.get(aiguillage.gabarit)
    if gabarit is None:
        return None, f"gabarit inconnu : {aiguillage.gabarit}"
    parametres = dict(aiguillage.parametres)
    for nom_parametre in gabarit.parametres_entites:
        valeur = parametres.get(nom_parametre)
        if valeur is None or valeur not in table:
            return None, valeur
        parametres[nom_parametre] = table[valeur]
    return construire_requete(gabarit.nom, parametres), None


async def interroger(
    graph: GraphMemory,
    traducteur: TraducteurQuestion,
    executeur: ExecuteurCypher,
    demande: InterrogationIn,
) -> InterrogationReponse:
    """Question française → aiguillage LLM → résolution serveur → exécution
    bornée → réponse formulée depuis les résultats. Si `demande.requete` est
    fournie (édition dans le monologue), rejeu direct **sans aucun appel
    LLM** — garde-fous compris."""
    noms = [n.nom for n in (await graph.graphe_complet(LIMITE_NOMS)).noeuds]

    if demande.requete is not None:
        requete = RequeteCypher(
            cypher=borner(demande.requete.cypher), parametres=demande.requete.parametres
        )
        resultats = await executeur.executer(requete)
        return InterrogationReponse(
            reponse=None,
            monologue=Monologue(requete=requete, resultats=resultats),
            vue=_construire_vue(resultats, noms, []),
            contexte=ContexteInterrogation(),
        )

    question = (demande.question or "").strip()
    aiguillage = await traducteur.aiguiller(question, demande.contexte)
    resolues, non_resolues = resoudre(aiguillage.mentions, noms)
    table = {r.mention: r.noeud for r in resolues}
    requete, inconnue = _requete_depuis_aiguillage(aiguillage, table)

    def _reponse(reponse: str | None, requete: RequeteCypher | None, resultats: list[dict],
                 resolues: list[MentionResolue]) -> InterrogationReponse:
        return InterrogationReponse(
            reponse=reponse,
            monologue=Monologue(
                aiguillage=aiguillage,
                resolues=resolues,
                non_resolues=non_resolues,
                requete=requete,
                resultats=resultats,
            ),
            vue=_construire_vue(resultats, noms, [r.noeud for r in resolues]),
            contexte=ContexteInterrogation(
                question_precedente=question, entites=[r.noeud for r in resolues]
            ),
        )

    if requete is None:
        if inconnue:
            return _reponse(
                f"Je ne connais pas « {inconnue} » dans le graphe : "
                "aucune entité de ce nom, la requête n'est pas partie.",
                None, [], resolues,
            )
        return _reponse(
            "Je n'ai pas su traduire cette question en requête sur le graphe.",
            None, [], resolues,
        )

    resultats = await executeur.executer(requete)
    if not resultats:
        return _reponse(REPONSE_SANS_RESULTAT, requete, resultats, resolues)
    formulation = await traducteur.formuler(question, resultats)
    return _reponse(formulation, requete, resultats, resolues)
