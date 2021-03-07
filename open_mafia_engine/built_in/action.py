from open_mafia_engine.core.engine import Action, ActionContext
from open_mafia_engine.state.game import GameState
from open_mafia_engine.state.voting import VoteTally


class InitGameAction(Action):
    """Initializes a normal game."""

    def __call__(self, game: GameState, context: ActionContext) -> None:
        # TODO: Implement!
        for actor in game.actors:
            actor.status["alive"] = True
        game.phase_num = 0
        game.status["lynch_tally"] = VoteTally()


class CancelAction(Action):
    """Action that cancels another action."""

    def __init__(self, target: Action, *, priority: float = 0, canceled: bool = False):
        if not isinstance(target, Action):
            raise ValueError(f"Expected Action, got {target!r}")
        super().__init__(priority=priority, canceled=canceled)
        self.target = target

    def __call__(self, game: GameState, context: ActionContext) -> None:
        self.target.canceled = True


class VoteAction(Action):
    """Action that votes for someone."""

    def __init__(
        self,
        source: str,
        target: str,
        tally_name: str,
        weight: int = 1,
        *,
        priority: float = 0,
        canceled: bool = False,
    ):
        super().__init__(priority=priority, canceled=canceled)
        self.source = source
        self.target = target
        self.weight = weight
        self.tally_name = tally_name

    def __call__(self, game: GameState, context: ActionContext) -> None:
        tally: VoteTally = game.status[self.tally_name]
        tally.add_vote(source=self.source, target=self.target, weight=self.weight)


class LynchAction(Action):
    """Action that mob-lynches a vote leader from a tally."""

    def __init__(
        self,
        *,
        tally_name: str = "lynch_tally",
        priority: float = 0,
        canceled: bool = False,
    ):
        super().__init__(priority=priority, canceled=canceled)
        self.tally_name = tally_name

    def __call__(self, game: GameState, context: ActionContext) -> None:
        tally: VoteTally = game.status[self.tally_name]
        target_name = tally.select_leader()

        # TODO: Change to 'death' instead of changing status directly
        target = game.actor_by_name(target_name)
        target.status["alive"] = False

        tally.clear()


class KillAction(Action):
    """Action from the `source` that kills the `target` Actor."""

    def __init__(
        self, source: str, target: str, *, priority: float = 0, canceled: bool = False
    ):
        if not isinstance(source, str):
            raise ValueError(f"Expected str, got {source!r}")
        if not isinstance(target, str):
            raise ValueError(f"Expected str, got {target!r}")
        super().__init__(priority=priority, canceled=canceled)
        self.source = source
        self.target = target

    def __call__(self, game: GameState, context: ActionContext) -> None:
        # TODO: Change to 'death' instead of changing status directly
        target = game.actor_by_name(self.target)
        target.status["alive"] = False


class PhaseChangeAction(Action):
    """Action that increments the current phase."""

    def __init__(
        self,
        *,
        priority: float = 0,
        canceled: bool = False,
    ):
        super().__init__(priority=priority, canceled=canceled)

    def __call__(self, game: GameState, context: ActionContext) -> None:
        game.phase_num += 1  # should automatically wrap around
