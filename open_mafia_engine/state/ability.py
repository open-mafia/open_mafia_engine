from typing import ClassVar, List
from open_mafia_engine.core.engine import EType, Subscriber

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


class ActivatedAbility(Ability):
    """Ability that is activated by the actor."""

    # TODO


class TriggeredAbility(Ability, Subscriber):
    """Ability that is triggered by an event."""

    sub_to: ClassVar[List[EType]] = []  # NOTE: Not a field!

    def __init__(self, **data) -> None:
        super().__init__(**data)
        self.subscribe_current(*self.sub_to)

    # @abstractmethod
    # def respond(self, e: Event) -> Optional[Action]:
    #     """Delayed response to the Event with an Action (or None)."""
    #     return None
