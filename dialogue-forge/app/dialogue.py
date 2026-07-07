"""Cœur du dialogue : l'orchestrateur d'un tour de conversation.

Pour chaque tour : injection de la mémoire → construction des messages →
boucle LLM/outils → diffusion phrase par phrase. L'extraction, elle, n'a plus
lieu par tour : elle attend la fermeture de la conversation (`clore_conversation`)
et ne mémorise que les tours de l'utilisateur (ADR 0011).

Le message système reste **constant** d'un tour à l'autre (uniquement le
prompt du persona) et la liste des outils n'est récupérée qu'une fois au
démarrage (`definir_outils`) : c'est ce qui garde le préfixe du prompt
identique octet pour octet d'un tour à l'autre et permet à llama.cpp de
réutiliser son cache de contexte plutôt que de tout retraiter à chaque tour.
Les faits mémoire, quand il y en a, sont injectés en aval sous forme d'un
message `user` de contexte, inséré juste avant le message utilisateur du
tour et **persisté** dans l'historique — c'est ce message qui varie, jamais
le système.
"""

import json
from collections.abc import AsyncIterator
from typing import Any

from app.llm.base import AppelOutil, DefinitionOutil, DeltaTexte, Message, MoteurLLM
from app.memoire.base import MoteurMemoire
from app.outils.base import MoteurOutils
from app.personas import Persona
from app.segmentation import SegmenteurPhrases

PREFIXE_CONTEXTE_MEMOIRE = "[Contexte mémoire — à utiliser sans le lire à voix haute]"

# Tours sans information neuve : on répond mais on ne les mémorise pas (ADR 0011).
# Seul un tour réduit à l'un de ces mots isolés est écarté ; « oui exactement »
# (plusieurs mots) est conservé.
BACKCHANNELS = frozenset(
    {
        "oui",
        "ouais",
        "non",
        "ok",
        "okay",
        "d'accord",
        "merci",
        "super",
        "parfait",
        "voilà",
        "voila",
        "bien",
    }
)


def _est_backchannel(texte: str) -> bool:
    normalise = texte.strip().lower().rstrip(" .!?…,")
    return normalise in BACKCHANNELS

# Bloc de consignes sur l'usage des outils, ajouté au prompt du persona.
# Constant d'un tour à l'autre et d'un persona à l'autre : toute variation
# ici invaliderait le cache de contexte du LLM (cf. docstring de module).
CONSIGNES_OUTILS = (
    "Consignes d'usage des outils :\n"
    "- Quand l'utilisateur demande ce qu'il t'a déjà dit, fait référence à une "
    "conversation passée ou à sa mémoire, appelle TOUJOURS l'outil `recall` avant "
    "de répondre. N'invente JAMAIS un souvenir : si `recall` ne renvoie rien, "
    "dis-le simplement.\n"
    "- Pour toute information du monde réel (météo, actualité, heure, agenda), "
    "utilise l'outil approprié plutôt que de deviner."
)


class Orchestrateur:
    def __init__(
        self,
        llm: MoteurLLM,
        memoire: MoteurMemoire,
        outils: MoteurOutils,
        max_iterations_outils: int = 5,
    ) -> None:
        self._llm = llm
        self._memoire = memoire
        self._outils = outils
        self._max_iterations_outils = max_iterations_outils
        self._outils_definitions: list[DefinitionOutil] = []

    def definir_outils(self, definitions: list[DefinitionOutil]) -> None:
        """Fixe une fois pour toutes les outils annoncés au LLM (appelé au
        démarrage, cf. lifespan de `app/main.py`) — jamais par tour."""
        self._outils_definitions = definitions

    def _construire_systeme(self, persona: Persona) -> Message:
        return {"role": "system", "content": f"{persona.prompt}\n\n{CONSIGNES_OUTILS}"}

    def _construire_message_contexte(self, faits: list[str]) -> Message | None:
        if not faits:
            return None
        rappel = "\n".join(f"- {fait}" for fait in faits)
        return {"role": "user", "content": f"{PREFIXE_CONTEXTE_MEMOIRE}\n{rappel}"}

    async def jouer_tour(
        self, persona: Persona, historique: list[Message], texte_utilisateur: str
    ) -> AsyncIterator[dict[str, Any]]:
        """Joue un tour et streame des événements NDJSON-ready :
        `{"type": "phrase", "texte": ...}` au fil de l'eau, puis un unique
        `{"type": "fin", "reponse": <texte complet>}`. Met à jour `historique`
        (contexte mémoire éventuel + tour utilisateur + réponse) et capture
        l'épisode en fin de tour."""
        # (a) Injection : faits pertinents à partir du texte utilisateur.
        faits = await self._memoire.rechercher(texte_utilisateur)
        message_contexte = self._construire_message_contexte(faits)

        # (b) Construction des messages du tour.
        messages: list[Message] = [self._construire_systeme(persona)]
        messages.extend(historique)
        if message_contexte is not None:
            messages.append(message_contexte)
        messages.append({"role": "user", "content": texte_utilisateur})
        debut_boucle_outils = len(messages)

        outils_definitions = self._outils_definitions

        # (c) + (d) Boucle LLM/outils, diffusion phrase par phrase de la réponse.
        reponse = ""
        tours_outils = 0
        while True:
            segmenteur = SegmenteurPhrases()
            contenu = ""
            appels: list[AppelOutil] = []
            async for evenement in self._llm.generer(messages, outils_definitions):
                if isinstance(evenement, DeltaTexte):
                    contenu += evenement.texte
                    for phrase in segmenteur.absorber(evenement.texte):
                        yield {"type": "phrase", "texte": phrase}
                else:
                    appels.append(evenement)

            if not appels:
                for phrase in segmenteur.terminer():
                    yield {"type": "phrase", "texte": phrase}
                reponse = contenu
                break

            if tours_outils >= self._max_iterations_outils:
                # Limite atteinte : on cesse de reboucler sur les outils.
                reponse = contenu
                break

            tours_outils += 1
            messages.append(
                {
                    "role": "assistant",
                    "content": contenu or None,
                    "tool_calls": [
                        {
                            "id": appel.id,
                            "type": "function",
                            "function": {"name": appel.nom, "arguments": appel.arguments},
                        }
                        for appel in appels
                    ],
                }
            )
            for appel in appels:
                try:
                    arguments = json.loads(appel.arguments) if appel.arguments else {}
                except json.JSONDecodeError:
                    arguments = {}
                resultat = await self._outils.appeler(appel.nom, arguments)
                messages.append(
                    {"role": "tool", "tool_call_id": appel.id, "content": resultat}
                )

        # (e) Historique et extraction de l'épisode. On persiste, dans l'ordre
        # exact où ils ont été envoyés au LLM, tous les messages de la boucle
        # d'outils (assistant+tool_calls, tool) avant le message final : le
        # tour suivant repart ainsi d'un préfixe identique à celui déjà vu
        # par le LLM, sans invalider son cache de contexte.
        if message_contexte is not None:
            historique.append(message_contexte)
        historique.append({"role": "user", "content": texte_utilisateur})
        historique.extend(messages[debut_boucle_outils:])
        historique.append({"role": "assistant", "content": reponse})

        yield {"type": "fin", "reponse": reponse}

    async def clore_conversation(
        self, historique: list[Message], nom: str, off_record: bool = False
    ) -> bool:
        """Fin de conversation : capture un unique épisode à partir des tours de
        l'**utilisateur** (l'assistant ne fait pas foi — ADR 0011). Écarte le
        message de contexte mémoire (rôle `user` mais injecté par nous) et les
        backchannels. Ne capture rien pour un persona off-record ou une
        conversation sans contenu utile. `nom` identifie l'épisode par la
        conversation (datée), non par le persona. Renvoie True si un épisode a
        été confié à la mémoire."""
        if off_record:
            return False
        tours = [
            m["content"]
            for m in historique
            if m["role"] == "user"
            and m["content"]
            and not m["content"].startswith(PREFIXE_CONTEXTE_MEMOIRE)
            and not _est_backchannel(m["content"])
        ]
        if not tours:
            return False
        contenu = "\n".join(f"Utilisateur : {tour}" for tour in tours)
        await self._memoire.capturer_episode(contenu=contenu, nom=nom)
        return True
