"""La boucle CodeAct (ADR 0013, ticket wayfinder 0032) : un pas = une Action
(bloc de code bash exécuté dans l'Atelier) et son observation réinjectée, ou
le Compte rendu final qui clôt la Tâche. Convention validée par la sonde du
0032 (`docs/wayfinder/notes/verdict-boucle-codeact-qwen3.6.md`) : le modèle
répond soit par un bloc ```bash```, soit par `TERMINÉ: <compte rendu>`."""

import re
from collections.abc import Awaitable, Callable

from app.atelier.base import Atelier, AtelierIndisponible
from app.llm.base import MoteurLLM
from app.schemas import PasJournal, Tache

EvenementBoucle = dict[str, object]

_MARQUEUR_FIN = "TERMINÉ:"
_BLOC_CODE = re.compile(r"```(?:bash|sh)?\s*\n(.*?)```", re.DOTALL)

_PROMPT_SYSTEME = (
    "Tu es le bras agissant d'un assistant vocal francophone. On te confie une "
    "Tâche en français ; tu la résous pas à pas dans un Atelier isolé (conteneur "
    "Docker jetable, bash + Python 3.12 + uv + ffmpeg, sans accès réseau).\n\n"
    "À chaque tour, réponds de l'une des deux façons suivantes, jamais les deux :\n"
    "- une seule Action à jouer, sous la forme d'un unique bloc ```bash ...``` "
    "(le résultat — sortie standard, erreur standard, code retour — te sera "
    "renvoyé comme observation) ;\n"
    "- si la Tâche est accomplie (ou impossible), une ligne commençant par "
    "« TERMINÉ: » suivie du Compte rendu en français, destiné à être restitué "
    "à la voix — pas de bloc de code dans ce cas."
)


def _extraire(reponse: str) -> tuple[str | None, str | None]:
    """Renvoie `(code, compte_rendu)` — exactement un des deux est renseigné,
    ou `(None, None)` si la réponse ne respecte ni l'un ni l'autre format."""
    marqueur = reponse.find(_MARQUEUR_FIN)
    if marqueur != -1:
        return None, reponse[marqueur + len(_MARQUEUR_FIN) :].strip()
    bloc = _BLOC_CODE.search(reponse)
    if bloc:
        return bloc.group(1).strip(), None
    return None, None


class BoucleCodeAct:
    """Orchestre le cycle observe-réfléchit-agit d'une Tâche dans son Atelier."""

    def __init__(self, moteur_llm: MoteurLLM, budget_pas: int) -> None:
        self._moteur_llm = moteur_llm
        self._budget_pas = budget_pas

    async def executer(
        self,
        tache: Tache,
        atelier: Atelier,
        sur_evenement: Callable[[EvenementBoucle], Awaitable[None] | None] | None = None,
    ) -> None:
        async def notifier(evenement: EvenementBoucle) -> None:
            if sur_evenement is None:
                return
            resultat = sur_evenement(evenement)
            if resultat is not None:
                await resultat

        messages = [
            {"role": "system", "content": _PROMPT_SYSTEME},
            {"role": "user", "content": tache.enonce},
        ]

        for _ in range(self._budget_pas):
            reponse = await self._moteur_llm.completer(messages)
            messages.append({"role": "assistant", "content": reponse})

            code, compte_rendu = _extraire(reponse)

            if compte_rendu is not None:
                tache.statut = "terminee"
                tache.compte_rendu = compte_rendu
                await notifier({"type": "terminee", "compte_rendu": compte_rendu})
                return

            if code is None:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Format non reconnu : réponds uniquement par un bloc "
                            "```bash ...``` ou par « TERMINÉ: <compte rendu> »."
                        ),
                    }
                )
                continue

            try:
                resultat = await atelier.executer(code)
            except AtelierIndisponible as exc:
                tache.statut = "echouee"
                tache.compte_rendu = f"L'Atelier est devenu indisponible : {exc}"
                await notifier({"type": "echouee", "compte_rendu": tache.compte_rendu})
                return

            tache.journal.append(PasJournal(code=code, resultat=resultat))
            await notifier({"type": "action", "code": code, "resultat": resultat})
            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Sortie standard :\n{resultat.sortie_standard}\n"
                        f"Erreur standard :\n{resultat.erreur_standard}\n"
                        f"Code retour : {resultat.code_retour}"
                    ),
                }
            )

        tache.statut = "echouee"
        tache.compte_rendu = f"Budget de pas épuisé ({self._budget_pas}) sans Compte rendu."
        await notifier({"type": "echouee", "compte_rendu": tache.compte_rendu})
