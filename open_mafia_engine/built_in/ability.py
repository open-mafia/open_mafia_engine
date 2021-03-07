from typing import List

from open_mafia_engine.state.ability import ActivatedAbility
from open_mafia_engine.state.constraint import Constraint


class VoteAbility(ActivatedAbility):
    """Absract vote ability."""

    type: str
    constraints: List[Constraint] = ["day"]


class LynchVoteAbility(VoteAbility):
    """Vote for a lynch target."""

    type: str = "lynch_vote"


class KillAbility(ActivatedAbility):
    """Kills the target."""

    type: str = "kill"
