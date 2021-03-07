from open_mafia_engine.core.engine import Action, ActionContext
from open_mafia_engine.state.actor import Actor
from open_mafia_engine.state.game import GameState


class InitGameAction(Action):
    """Initializes a normal game."""

    def __call__(self, game: GameState, context: ActionContext) -> None:
        # TODO: Implement!
        for actor in game.actors:
            actor.status["alive"] = True
        game.phase_num = 0


class CancelAction(Action):
    """Action that cancels another action."""

    def __init__(self, target: Action, *, priority: float = 0, canceled: bool = False):
        if not isinstance(target, Action):
            raise ValueError(f"Expected Action, got {target!r}")
        super().__init__(priority=priority, canceled=canceled)
        self.target = target

    def __call__(self, game: GameState, context: ActionContext) -> None:
        self.target.canceled = True


class KillAction(Action):
    """Action that kills the `target` Actor."""

    def __init__(self, target: Actor, *, priority: float = 0, canceled: bool = False):
        if not isinstance(target, Actor):
            raise ValueError(f"Expected Actor, got {target!r}")
        super().__init__(priority=priority, canceled=canceled)
        self.target = target

    def __call__(self, game: GameState, context: ActionContext) -> None:
        self.target.status["alive"] = False
