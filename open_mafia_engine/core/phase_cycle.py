from typing import Optional, Union
from open_mafia_engine.core.event_system import (
    EPostAction,
    EPreAction,
    Event,
    Subscriber,
    handler,
    Action,
    ActionResolutionType,
)
from open_mafia_engine.core.game_object import GameObject


class Phase(GameObject):
    def __init__(
        self,
        game,
        /,
        name: str,
        action_resolution: str = "instant",
    ):
        super().__init__(game)

        self.name = name
        self.action_resolution = ActionResolutionType(action_resolution)


class ETryPhaseChange(Event):
    def __init__(self, game, /, new_phase: Optional[Phase] = None):
        self.new_phase = new_phase
        super().__init__(game)


class PhaseChangeAction(Action):
    """Action to change the phase."""

    def __init__(self, game, /, *, priority: float = 0.0, canceled: bool = False):
        super().__init__(game, priority=priority, canceled=canceled)

    class Pre(EPreAction):
        pass

    class Post(EPostAction):
        pass


class AbstractPhaseCycle(Subscriber):
    """Interface for a phase cycle."""
