from typing import Optional, List

from open_mafia_engine.core.engine import ActionContext
from open_mafia_engine.state.constraint import Constraint
from open_mafia_engine.state.game import GameState


class ActorAliveConstraint(Constraint, default=True):
    """Actor must be alive. Default is True."""

    type: str = "actor_alive"
    value: Optional[bool] = True

    class Action(Constraint.Action):
        def __call__(self, game_state: GameState, context: ActionContext) -> None:
            # TODO: Implement!
            # self.target.canceled = True
            pass


class TargetAliveConstraint(Constraint, default=True):
    """Target must be alive. Default is True."""

    type: str = "target_alive"
    value: Optional[bool] = True

    class Action(Constraint.Action):
        def __call__(self, game_state: GameState, context: ActionContext) -> None:
            # TODO: Implement!
            # self.target.canceled = True
            pass


class ActionLimitPerPhaseConstraint(Constraint, default=True):
    """Limits the numbers of actions taken per phase. Default is 1."""

    type: str = "action_limit"
    n_actions: Optional[int] = 1

    class Action(Constraint.Action):
        def __call__(self, game_state: GameState, context: ActionContext) -> None:
            # TODO: Implement!
            # self.target.canceled = True
            pass


class PhaseConstraint(Constraint):
    """Ability may be used only during this phase."""

    type: str = "phase"
    phases: List[str]

    class Action(Constraint.Action):
        def __call__(self, game_state: GameState, context: ActionContext) -> None:
            if game_state.current_phase.name not in self.parent.phases:
                self.target.canceled = True


class KeyPhaseConstraint(PhaseConstraint):
    """All abilities with the `key` can only be used N times per phase.

    Most notably, this is useful for faction-wide kills/abilities.

    Attributes
    ----------
    type : "key_phase_limited"
    key : str
        The key to constrain to. This can be arbitrary, e.g. "faction-mafia"
    phases : List
        The phases to use. These must be a subset of the defined phases.
    uses : int
        The number of faction uses per each phase.
    """

    type: str = "key_phase_limited"
    key: str
    phases: List[str]
    uses: int = 1

    class Action(Constraint.Action):
        def __call__(self, game_state: GameState, context: ActionContext) -> None:

            if game_state.current_phase.name not in self.parent.phases:
                self.target.canceled = True
                return

            # TODO: Implement checking for uses in the key
            # self.target.canceled = True


class NShotConstraint(Constraint):
    """Ability may only be used N times total during the game."""

    type: str = "n_shot"
    uses: int

    class Action(Constraint.Action):
        def __call__(self, game_state: GameState, context: ActionContext) -> None:
            # TODO: Implement!
            # self.target.canceled = True
            pass
