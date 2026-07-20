from app.llm.base import Message, MoteurLLM

_REPONSE_PAR_DEFAUT = "TERMINÉ: (LLM factice) rien à signaler."


class MoteurLLMFactice(MoteurLLM):
    """Zéro réseau : rend des réponses scriptées dans l'ordre (pattern
    `AtelierFactice`) ; une fois la liste épuisée, clôt la Tâche par une
    réponse par défaut plutôt que de lever — cohérent avec le comportement de
    `AtelierFactice` sans résultat préparé."""

    def __init__(self, reponses: list[str] | None = None) -> None:
        self._reponses = list(reponses or [])
        self.messages_recus: list[list[Message]] = []

    async def completer(self, messages: list[Message]) -> str:
        self.messages_recus.append(list(messages))
        if self._reponses:
            return self._reponses.pop(0)
        return _REPONSE_PAR_DEFAUT
