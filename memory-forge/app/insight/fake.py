from app.insight.base import GenerateurInsight
from app.schemas import CondenseGraphe


class GenerateurInsightFactice(GenerateurInsight):
    """Générateur déterministe, zéro réseau : construit un paragraphe français
    plausible directement à partir du condensé, pour les tests et le
    développement sans LLM."""

    async def generer(self, condense: CondenseGraphe) -> str:
        if condense.nb_entites == 0:
            return "La mémoire est vide pour l'instant : aucune entité n'y a encore été consignée."

        phrase = (
            f"La mémoire retient aujourd'hui {condense.nb_entites} entités reliées par "
            f"{condense.nb_faits} faits"
        )
        if condense.nb_faits_obsoletes:
            phrase += f", dont {condense.nb_faits_obsoletes} désormais obsolètes"
        phrase += "."

        if condense.sujets:
            premier = condense.sujets[0]
            phrase += (
                f" Le sujet le plus marquant tourne autour de {premier.nom}, "
                f"qui rassemble {premier.taille} entités."
            )

        if condense.ponts:
            phrase += (
                f" {condense.ponts[0]} se distingue en faisant le pont entre plusieurs sujets."
            )

        return phrase
