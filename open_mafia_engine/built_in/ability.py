from typing import ClassVar, List, Optional
from open_mafia_engine.built_in.action import LynchAction, PhaseChangeAction
from open_mafia_engine.core.engine import EType, Event, PreActionEvent

from open_mafia_engine.state.ability import ActivatedAbility, TriggeredAbility
from open_mafia_engine.state.constraint import Constraint


DEFAULT_LYNCH_TALLY = "lynch_tally"


class VoteAbility(ActivatedAbility):
    """Absract vote ability."""

    type: str
    tally_name: str
    constraints: List[Constraint] = ["day"]


class LynchVoteAbility(VoteAbility):
    """Vote for a lynch target."""

    type: str = "lynch_vote"
    tally_name: str = DEFAULT_LYNCH_TALLY


class KillAbility(ActivatedAbility):
    """Kills the target."""

    type: str = "kill"
