from app.actions.base import ActionRunner
from app.catalog import Action


class FakeRunner(ActionRunner):
    """Exécuteur factice : n'exécute rien, garde trace des actions lancées —
    tests et dev sans toucher au bureau."""

    def __init__(self) -> None:
        self.launched: list[Action] = []

    def run(self, action: Action) -> str:
        self.launched.append(action)
        return f"C'est fait : {action.description}"
