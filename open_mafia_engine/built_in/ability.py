from typing import ClassVar, List, Optional
from open_mafia_engine.built_in.action import (
    KillAction,
    LynchAction,
    PhaseChangeAction,
    VoteAction,
)
from open_mafia_engine.core.engine import EType, Event, PreActionEvent

from open_mafia_engine.state.ability import (
    Ability,
    ActivatedAbility,
    ActivationEvent,
    TriggeredAbility,
)
from open_mafia_engine.state.actor import Actor
from open_mafia_engine.state.constraint import Constraint


DEFAULT_LYNCH_TALLY = "lynch_tally"


class VoteAbility(ActivatedAbility):
    """Absract vote ability."""

    type: str = "vote"
    tally_name: str
    constraints: List[Constraint] = ["day"]

    def respond(self, e: Event) -> Optional[VoteAction]:
        """Response to an ActivationEvent. Override this!"""

        if isinstance(e, ActivationEvent):
            abil: Ability = e.actor.role.ability_by_name(e.ability_name)
            if abil is self:
                return VoteAction(
                    source=e.actor.name,
                    target=e.params["target"],
                    tally_name=self.tally_name,
                )
        return None


class LynchVoteAbility(VoteAbility):
    """Vote for a lynch target."""

    type: str = "lynch_vote"
    tally_name: str = DEFAULT_LYNCH_TALLY


class KillAbility(ActivatedAbility):
    """Kills the target."""

    type: str = "kill"

    def respond(self, e: Event) -> Optional[KillAction]:
        """Response to an ActivationEvent. Override this!"""

        if isinstance(e, ActivationEvent):
            abil: Ability = e.actor.role.ability_by_name(e.ability_name)
            if abil is self:
                return KillAction(
                    source=e.actor.name,
                    target=e.params["target"],
                    tally_name=self.tally_name,
                )
        return None


class PhaseEndLynchAbility(TriggeredAbility):
    """Lynch at the end of the phase (right before phase change).

    TODO: Make it possible to choose phases...
    """

    type: str = "phase_end_lynch"
    tally_name: str = "lynch_tally"

    sub_to: ClassVar[List[EType]] = [PreActionEvent]  # NOTE: Not a field!

    def respond(self, e: Event) -> Optional[LynchAction]:
        """Delayed response to the Event with an Action (or None)."""
        if isinstance(e, PreActionEvent) and isinstance(e.action, PhaseChangeAction):
            return LynchAction(tally_name=self.tally_name)
