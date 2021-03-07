from open_mafia_engine.core.engine import Action, ActionContext
from open_mafia_engine.state.game import GameState


class CancelAction(Action):
    """Action that cancels another action."""

    def __init__(self, target: Action, *, priority: float = 0, canceled: bool = False):
        if not isinstance(target, Action):
            raise ValueError(f"Expected Action, got {target!r}")
        super().__init__(priority=priority, canceled=canceled)
        self.target = target

    def __call__(self, game: GameState, context: ActionContext) -> None:
        self.target.canceled = True
