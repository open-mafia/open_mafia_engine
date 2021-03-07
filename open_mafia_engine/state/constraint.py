from __future__ import annotations
from typing import List, Optional

from open_mafia_engine.util.hook import HookModel


class Constraint(HookModel):
    """Base constraint data type.

    To create a constraint, subclass this, change the 'type' default value,
    and make sure it's imported.
    """

    type: str

    class Hook:
        subtypes = {}
        builtins = {}
        defaults = {}


class ActorAliveConstraint(Constraint, default=True):
    """Actor must be alive. Default is True."""

    type: str = "actor_alive"
    value: Optional[bool] = True


class TargetAliveConstraint(Constraint, default=True):
    """Target must be alive. Default is True."""

    type: str = "target_alive"
    value: Optional[bool] = True


class ActionLimitPerPhaseConstraint(Constraint, default=True):
    """Limits the numbers of actions taken per phase. Default is 1."""

    type: str = "action_limit"
    n_actions: Optional[int] = 1


class PhaseConstraint(Constraint):
    """Ability may be used only during this phase."""

    type: str = "phase"
    phases: List[str]


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


class NShotConstraint(Constraint):
    """Ability may only be used N times total during the game."""

    type: str = "n_shot"
    uses: int
