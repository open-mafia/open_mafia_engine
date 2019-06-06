"""Various ability restrictions."""

import typing
from mafia.core.ability import Restriction, ActivatedAbility, TryActivateAbility
from mafia.state.game import PhaseState

from mafia.core.event import Subscriber, Event, Action


class PhaseUse(Restriction):
    """Allows use only in certain phases.
    
    Attributes
    ----------
    phase_state : PhaseState
        The phase state to check against.
    allowed_phases : list
        The phases when it is legal to use the ability.
    """

    def __init__(
        self,
        phase_state: PhaseState,
        allowed_phases: typing.List = [],
        owner: ActivatedAbility = None,
    ):
        super().__init__(owner=owner)
        self.phase_state = phase_state
        self.allowed_phases = list(allowed_phases)

    def is_legal(self, ability: ActivatedAbility, **kwargs) -> bool:
        if self.phase_state.current in self.allowed_phases:
            return True
        return False


class NUse(Restriction, Subscriber):
    """Allows limited number of uses.

    Note that this listens to use attempts (:class:`TryActivateAbility`) 
    rather than checks for legality (:meth:`is_legal`) or successful uses.

    Attributes
    ----------
    max_uses : int
        The maximum number of uses. Default is 1.
    current_uses : int
        The current number of uses. Default is 0.
    """

    class IncrementUses(Action):
        """Increments the use count of the parent restriction."""

        def __init__(self, n_use_restriction):
            self.n_use_restriction = n_use_restriction

        @property
        def priority(self) -> float:
            """Minimum possible priority to always be at end of stack."""
            return float("-inf")

        def __execute__(self) -> bool:
            self.n_use_restriction.current_uses += 1
            return True

    def __init__(
        self, max_uses: int = 1, current_uses: int = 0, owner: ActivatedAbility = None
    ):
        super().__init__(owner=owner)
        self.max_uses = max_uses
        self.current_uses = current_uses

        self.subscribe_to(TryActivateAbility)

    def respond_to_event(self, event: Event) -> typing.Optional[Action]:
        if isinstance(event, TryActivateAbility):
            if event.ability is self.owner:
                # If our owner ability is being used, we increment our use count
                # This will run at the end of all actions, so we increment at the end
                return self.IncrementUses(self)
        return None

    def is_legal(self, ability: ActivatedAbility, **kwargs) -> bool:
        return self.current_uses < self.max_uses
