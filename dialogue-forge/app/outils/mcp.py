"""Adaptateur outils réel : client MCP streamable HTTP, agrégeant plusieurs forges.

**Validé en réel le 2026-07-07** contre les serveurs MCP de time-, world- et
memory-forge (listage agrégé et appel routé, notamment `weather` du
world-forge). Aucun test ne l'instancie ni ne le joint (zéro réseau dans la
suite automatisée).

Le forge est *client* MCP (écart assumé : il n'expose aucun serveur MCP). On
ouvre une session par URL à la demande, on agrège les outils de tous les
serveurs et on convertit chaque outil MCP vers le format OpenAI tools ; les
appels sont routés vers le serveur propriétaire de l'outil.

**Tolérance à l'échec et reprise (ticket 0043)** : constaté au réel le
2026-07-20, une seule forge MCP injoignable au démarrage faisait mourir tout
le Dialogue Forge (l'exception remontait jusqu'au lifespan de `app/main.py`,
et `restart: unless-stopped` transformait l'échec en boucle de redémarrage).
`lister_outils` ne laisse donc plus jamais remonter d'exception : une forge en
échec voit simplement ses outils retirés du catalogue (dégradation
silencieuse côté LLM — décision actée, le prompt système n'en dit rien pour
ne pas invalider le cache de contexte de llama.cpp). Chaque URL saine garde
ses définitions en cache ; `rafraichir` ne retente que les URLs en échec, au
plus une fois par `palier_reprise_s`, appelé par l'orchestrateur en tout
début de tour (jamais de tâche de fond asyncio) — les forges saines ne sont
donc pas re-questionnées à chaque reprise.
"""

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from app.llm.base import DefinitionOutil
from app.outils.base import MoteurOutils

logger = logging.getLogger(__name__)


def _vers_format_openai(nom: str, description: str | None, schema: dict) -> DefinitionOutil:
    return {
        "type": "function",
        "function": {
            "name": nom,
            "description": description or "",
            "parameters": schema or {"type": "object", "properties": {}},
        },
    }


@dataclass
class _EtatUrl:
    """Dernier état connu d'une URL. `definitions` porte les outils (au format
    OpenAI) de la dernière écoute réussie ; `erreur` non-None signifie que
    l'URL est actuellement en échec (auquel cas `definitions` est vide) et
    `derniere_tentative_s` date cet échec pour le comparer au palier."""

    definitions: list[DefinitionOutil] = field(default_factory=list)
    erreur: str | None = None
    derniere_tentative_s: float = 0.0

    @property
    def en_echec(self) -> bool:
        return self.erreur is not None


class OutilsMCP(MoteurOutils):
    def __init__(
        self,
        urls: list[str],
        palier_reprise_s: float = 60.0,
        horloge: Callable[[], float] = time.monotonic,
    ) -> None:
        self._urls = urls
        self._palier_reprise_s = palier_reprise_s
        # `horloge` n'est injectable que pour que les tests contrôlent le temps
        # sans avoir à dormir réellement `palier_reprise_s` secondes.
        self._horloge = horloge
        # nom d'outil → URL du serveur qui le porte ; reconstruit à chaque
        # `lister_outils`/`rafraichir` réussi, toujours cohérent avec le
        # catalogue renvoyé en dernier.
        self._routage: dict[str, str] = {}
        # url → dernier état connu (peuplé après le premier lister_outils).
        self._etats: dict[str, _EtatUrl] = {}

    async def _lister_une(self, url: str) -> list[DefinitionOutil]:
        """Ouvre une session vers `url` et renvoie ses outils, déjà convertis au
        format OpenAI tools. Laisse remonter toute exception réseau/protocole —
        c'est aux appelants (`lister_outils`, `rafraichir`) de décider de la
        tolérance."""
        async with (
            streamablehttp_client(url) as (lecture, ecriture, _),
            ClientSession(lecture, ecriture) as session,
        ):
            await session.initialize()
            outils = (await session.list_tools()).tools
        return [
            _vers_format_openai(outil.name, outil.description, outil.inputSchema)
            for outil in outils
        ]

    def _reconstruire_routage_et_catalogue(self) -> list[DefinitionOutil]:
        """Recompose le catalogue complet et le routage à partir des états en
        cache, dans l'ordre stable de `self._urls`."""
        definitions: list[DefinitionOutil] = []
        self._routage.clear()
        for url in self._urls:
            etat = self._etats.get(url)
            if etat is None or etat.en_echec:
                continue
            for definition in etat.definitions:
                self._routage[definition["function"]["name"]] = url
            definitions.extend(etat.definitions)
        return definitions

    async def lister_outils(self) -> list[DefinitionOutil]:
        for url in self._urls:
            try:
                definitions = await self._lister_une(url)
            except Exception as erreur:
                logger.warning(
                    "Forge d'outils injoignable, ses outils sont retirés du catalogue : %s (%s)",
                    url,
                    erreur,
                )
                self._etats[url] = _EtatUrl(
                    erreur=str(erreur), derniere_tentative_s=self._horloge()
                )
                continue
            self._etats[url] = _EtatUrl(definitions=definitions)
        return self._reconstruire_routage_et_catalogue()

    async def rafraichir(self) -> list[DefinitionOutil] | None:
        """Retente les URLs en échec si le palier est écoulé. Renvoie None au
        moindre doute (rien en échec, palier pas écoulé, aucune reprise) — le
        chemin nominal ne coûte rien (pas de session ouverte)."""
        urls_en_echec = [url for url in self._urls if self._etats.get(url, _EtatUrl()).en_echec]
        if not urls_en_echec:
            return None

        maintenant = self._horloge()
        # Toutes les URLs en échec partagent le même rythme de reprise : on ne
        # retente que si la plus ancienne tentative a dépassé le palier.
        derniere_tentative = min(self._etats[url].derniere_tentative_s for url in urls_en_echec)
        if maintenant - derniere_tentative < self._palier_reprise_s:
            return None

        au_moins_une_reprise = False
        for url in urls_en_echec:
            try:
                definitions = await self._lister_une(url)
            except Exception as erreur:
                self._etats[url] = _EtatUrl(erreur=str(erreur), derniere_tentative_s=maintenant)
                continue
            logger.info("Forge d'outils de retour : %s (%d outil(s))", url, len(definitions))
            self._etats[url] = _EtatUrl(definitions=definitions)
            au_moins_une_reprise = True

        if not au_moins_une_reprise:
            return None

        return self._reconstruire_routage_et_catalogue()

    def etat_forges(self) -> list[dict]:
        """Point d'audit (ticket 0043) : l'état de chaque forge, dans l'ordre de
        `self._urls`. Utilisé par `/health` pour rendre visible une forge tombée
        sans avoir à lire un traceback."""
        resultat = []
        for url in self._urls:
            etat = self._etats.get(url)
            if etat is None:
                # Jamais listée (avant le premier `lister_outils`) : on ne
                # prétend rien savoir de son état.
                resultat.append({"url": url, "etat": "inconnu", "outils": 0, "erreur": None})
            elif etat.en_echec:
                resultat.append(
                    {"url": url, "etat": "injoignable", "outils": 0, "erreur": etat.erreur}
                )
            else:
                resultat.append(
                    {"url": url, "etat": "ok", "outils": len(etat.definitions), "erreur": None}
                )
        return resultat

    async def appeler(self, nom: str, arguments: dict[str, Any]) -> str:
        url = self._routage.get(nom)
        if url is None:
            return f"Outil inconnu : {nom}"
        async with (
            streamablehttp_client(url) as (lecture, ecriture, _),
            ClientSession(lecture, ecriture) as session,
        ):
            await session.initialize()
            resultat = await session.call_tool(nom, arguments)
        morceaux = [
            bloc.text for bloc in resultat.content if getattr(bloc, "type", None) == "text"
        ]
        return "\n".join(morceaux) if morceaux else json.dumps(
            [bloc.model_dump() for bloc in resultat.content], ensure_ascii=False
        )
