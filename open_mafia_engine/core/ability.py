from typing import List
from pydantic import validator

from open_mafia_engine.util.hook import HookModel

from .constraint import Constraint


class Ability(HookModel):
    """A role's ability.

    Attributes
    ----------
    type : str
        This is the ability type, which will be looked up from available ones.
    name : str
        Human-readable name of the ability.
    desc : str = "<no description>"
        Human-readable description of the ability.
    constriants : List[Constraint]
        Constraints on the use of the ability.
        Note: default constraints will be added afterwards by parse_list, unless
        manually changed (e.g. 'actor alive', 'target alive' and 'one action per phase')
    """

    type: str
    name: str
    desc: str = "<no description>"
    constraints: List[Constraint] = []

    class Hook:
        subtypes = {}
        builtins = {}
        defaults = {}

    _chk_constraints_pre = validator(
        "constraints", pre=True, always=True, allow_reuse=True
    )(Constraint.parse_list)


class VoteAbility(Ability):
    """Absract vote ability."""

    type: str
    constraints: List[Constraint] = ["day"]


class LynchVoteAbility(VoteAbility):
    """Vote for a lynch target."""

    type: str = "lynch_vote"


class KillAbility(Ability):
    """Kills the target."""

    type: str = "kill"
