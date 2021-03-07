from abc import abstractmethod
from typing import Any, ClassVar, Dict, List, Optional
from open_mafia_engine.core.engine import Action, EType, Event, Subscriber

# from open_mafia_engine.state.actor import Actor  # CANNOT import

from pydantic import validator

from open_mafia_engine.util.hook import HookModel

from .constraint import Constraint


class Ability(HookModel, Subscriber):
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

    sub_to: ClassVar[List[EType]] = []  # NOTE: Not a field!

    class Hook:
        subtypes = {}
        builtins = {}
        defaults = {}

    def sub(self):
        """Runs the subscription."""
        self.subscribe_current(*self.sub_to)

    def __eq__(self, other):
        return other is self

    _chk_constraints_pre = validator(
        "constraints", pre=True, always=True, allow_reuse=True
    )(Constraint.parse_list)


class ActivationEvent(Event):
    """Activation of an ability by an Actor.

    Attributes
    ----------
    actor : Actor
    ability_name : str
        The name of the ability.
    params : dict
        Keyword abilities.
    """

    def __init__(self, actor, ability_name: str, **params: Dict[str, Any]):
        self.actor = actor
        self.ability_name = ability_name
        self.params = params


class ActivatedAbility(Ability):
    """Ability that is activated by the actor."""

    sub_to: ClassVar[List[EType]] = [ActivationEvent]  # NOTE: Not a field!

    @abstractmethod
    def respond(self, e: Event) -> Optional[Action]:
        """Response to an ActivationEvent. Override this!"""

        if isinstance(e, ActivationEvent):
            actor = e.actor
            abil = actor.role.ability_by_name(e.ability_name)
            if abil is self:
                # Return Action here!
                return None
        return None


class TriggeredAbility(Ability):
    """Ability that is triggered by an event."""

    sub_to: ClassVar[List[EType]] = []  # NOTE: Not a field!

    @abstractmethod
    def respond(self, e: Event) -> Optional[Action]:
        """Delayed response to the Event with an Action (or None)."""
        return None
