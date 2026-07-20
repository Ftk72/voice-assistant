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

Garde-fou d'écho (ticket 0044) : une annonce spontanée (fin de Tâche,
échéance de minuteur) peut tomber pendant une conversation micro vif, être
captée par le micro et transcrite par le STT comme si l'utilisateur avait
parlé. `clore_conversation` écarte alors ce tour fantôme via `_est_echo`.
C'est un **filet de sécurité de dernier recours**, purement textuel et local
à cette fonction — il ne remplace pas le correctif structurel (le canal de
l'annonce, traité côté transport/pont hôte, cf. ticket 0044) : il ne fait que
limiter les dégâts sur la mémoire si ce correctif est absent ou insuffisant.
"""

import difflib
import json
import re
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


# Similarité (SequenceMatcher, ratio 0-1) au-delà de laquelle un tour
# utilisateur est considéré comme un écho du tour assistant qui le précède.
# 0.8 tolère les pertes usuelles d'un STT (casse, ponctuation, une élision ou
# deux) tout en laissant passer une reformulation qui ne réemploie que
# quelques mots de l'assistant (cf. tests/test_garde_fou_echo.py) : un humain
# qui reformule change la structure de la phrase, un micro qui réentend les
# enceintes la restitue quasi telle quelle.
SEUIL_ECHO = 0.8

# Plancher de longueur (caractères, texte normalisé) en dessous duquel on ne
# tente même pas la comparaison : sur un texte très court, quelques
# caractères communs suffisent à gonfler artificiellement le ratio de
# SequenceMatcher (ex. « oui » vs un tour assistant qui contient « oui »
# ailleurs). Ces tours très courts sont de toute façon déjà couverts par le
# filtre des backchannels ; ce n'est pas au garde-fou d'écho de les juger.
PLANCHER_LONGUEUR_ECHO = 8


def _normaliser_pour_comparaison(texte: str) -> str:
    """Minuscules, ponctuation retirée, espaces multiples réduits — le STT ne
    restitue ni la casse ni la ponctuation de ce que dit la synthèse."""
    sans_ponctuation = re.sub(r"[^\w\s]", " ", texte.lower())
    return re.sub(r"\s+", " ", sans_ponctuation).strip()


def _est_echo(texte_utilisateur: str, texte_assistant: str) -> bool:
    """Un tour `user` qui reprend, en substance, le tour `assistant` qui le
    précède immédiatement est un écho (micro qui réentend les enceintes) et
    non une parole de l'utilisateur — cf. docstring de module."""
    if not texte_assistant:
        # Un texte assistant vide ne peut être la source d'aucun écho.
        return False
    normalise_utilisateur = _normaliser_pour_comparaison(texte_utilisateur)
    normalise_assistant = _normaliser_pour_comparaison(texte_assistant)
    if len(normalise_utilisateur) < PLANCHER_LONGUEUR_ECHO:
        return False
    ratio = difflib.SequenceMatcher(None, normalise_utilisateur, normalise_assistant).ratio()
    return ratio >= SEUIL_ECHO


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
        self,
        persona: Persona,
        historique: list[Message],
        texte_utilisateur: str,
        *,
        voix: str | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Joue un tour et streame des événements NDJSON-ready :
        `{"type": "phrase", "texte": ...}` au fil de l'eau, puis un unique
        `{"type": "fin", "reponse": <texte complet>}`. Met à jour `historique`
        (contexte mémoire éventuel + tour utilisateur + réponse) et capture
        l'épisode en fin de tour.

        `voix` déroge à la voix du persona pour ce tour (ADR 0012 décision 5) :
        None = voix du persona ; sinon la voix dérogée est portée par chaque
        phrase du flux, à charge du transport de l'appliquer au TTS."""
        voix_du_tour = voix or persona.voix

        # (0) Reprise à chaud (ticket 0043) : retente les forges d'outils
        # tombées, au plus une fois par palier (cf. `OutilsMCP.rafraichir`).
        # `None` = rien n'a changé, on ne touche à rien ; ce n'est que quand une
        # forge revient réellement que le catalogue — donc le préfixe du prompt
        # système — bouge, ce qui est le seul moment où invalider le cache de
        # contexte du LLM est justifié.
        catalogue_rafraichi = await self._outils.rafraichir()
        if catalogue_rafraichi is not None:
            self._outils_definitions = catalogue_rafraichi

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
                        yield {"type": "phrase", "texte": phrase, "voix": voix_du_tour}
                else:
                    appels.append(evenement)

            if not appels:
                for phrase in segmenteur.terminer():
                    yield {"type": "phrase", "texte": phrase, "voix": voix_du_tour}
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
                # Le module d'interface (A4) affiche les outils appelés ; le DF
                # remplace l'étage LLM, donc c'est son flux — pas RTVI — qui doit
                # porter l'info (ticket 0008). Émis au déclenchement de l'appel.
                yield {"type": "outil", "nom": appel.nom}
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

    def interrompre(self, historique: list[Message], prefixe_prononce: str) -> bool:
        """Interruption (ADR 0012 décision 3) : le transport sait combien de
        phrases il a jouées et signale le préfixe réellement prononcé. On tronque
        le **dernier tour assistant** à ce préfixe pour que le LLM ne référence
        jamais l'inaudible au tour suivant — la cohérence *live*, pas le graphe
        (la mémoire est user-only de toute façon, ADR 0011). Renvoie True si un
        tour assistant a été tronqué."""
        for message in reversed(historique):
            if message["role"] == "assistant":
                message["content"] = prefixe_prononce
                return True
        return False

    async def clore_conversation(
        self, historique: list[Message], nom: str, off_record: bool = False
    ) -> bool:
        """Fin de conversation : capture un unique épisode à partir des tours de
        l'**utilisateur** (l'assistant ne fait pas foi — ADR 0011). Écarte le
        message de contexte mémoire (rôle `user` mais injecté par nous), les
        backchannels, et — garde-fou de dernier recours, cf. docstring de
        module — tout tour `user` qui n'est que l'écho du tour `assistant`
        immédiatement précédent (annonce spontanée captée par le micro et
        transcrite par erreur comme une parole de l'utilisateur). Ne capture
        rien pour un persona off-record ou une conversation sans contenu
        utile. `nom` identifie l'épisode par la conversation (datée), non par
        le persona. Renvoie True si un épisode a été confié à la mémoire."""
        if off_record:
            return False
        tours: list[str] = []
        dernier_assistant = ""
        for message in historique:
            if message["role"] == "assistant":
                dernier_assistant = message["content"] or ""
                continue
            if message["role"] != "user" or not message["content"]:
                continue
            contenu = message["content"]
            if contenu.startswith(PREFIXE_CONTEXTE_MEMOIRE):
                continue
            if _est_backchannel(contenu):
                continue
            if _est_echo(contenu, dernier_assistant):
                continue
            tours.append(contenu)
        if not tours:
            return False
        contenu = "\n".join(f"Utilisateur : {tour}" for tour in tours)
        await self._memoire.capturer_episode(contenu=contenu, nom=nom)
        return True
