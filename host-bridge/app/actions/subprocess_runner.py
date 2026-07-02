"""Exécuteur réel — jamais exécuté à ce jour (pattern GraphitiMemory).

Lance la commande de l'action pour la plateforme courante, via un argv explicite
(jamais `shell=True` : pas d'injection possible, seule la liste blanche existe) et
sans attendre (`Popen`) — ouvrir une application ne doit pas bloquer le Pont.
"""

import subprocess
import sys

from app.actions.base import ActionRunner
from app.catalog import Action


class SubprocessRunner(ActionRunner):
    def run(self, action: Action) -> str:
        argv = action.command_for(sys.platform)
        if argv is None:
            return f"« {action.name} » est indisponible sur cette plateforme."
        # Jamais shell=True : l'argv du catalogue est lancé tel quel, sans interprétation.
        subprocess.Popen(argv)
        return f"C'est fait : {action.description}"
