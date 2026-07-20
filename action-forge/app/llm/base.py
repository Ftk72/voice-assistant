"""Port du cerveau de la boucle CodeAct.

Contrairement au port `MoteurLLM` de dialogue-forge (streaming, appels
d'outils natifs), ici un pas de la boucle est un unique aller-retour texte :
le modèle répond soit par une Action (bloc de code bash), soit par le Compte
rendu final (qualifié au ticket wayfinder 0032, note
`docs/wayfinder/notes/verdict-boucle-codeact-qwen3.6.md`)."""

from abc import ABC, abstractmethod

# Un message au format OpenAI : {"role": "system"|"user"|"assistant", "content": str}.
Message = dict[str, str]


class MoteurLLM(ABC):
    """Port du cerveau : une complétion non streamée par pas de boucle."""

    @abstractmethod
    async def completer(self, messages: list[Message]) -> str:
        """Renvoie le texte complet de la réponse du modèle pour `messages`."""
