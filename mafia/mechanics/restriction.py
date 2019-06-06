"""Various ability restrictions."""

import typing
from mafia.core.ability import Restriction, ActivatedAbility  # , TryActivateAbility
from mafia.state.game import PhaseState

# from mafia.core.event import Subscriber, Event


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
