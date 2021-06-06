from __future__ import annotations

from typing import Optional

from open_mafia_engine.core.enums import ActionResolutionType
from open_mafia_engine.core.event_system import (
    Action,
    EPostAction,
    EPreAction,
    Event,
    Subscriber,
    handler,
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

        self._name = name
        self._action_resolution = ActionResolutionType(action_resolution)

    @property
    def name(self) -> str:
        return self._name

    @property
    def action_resolution(self) -> ActionResolutionType:
        return self._action_resolution

    @action_resolution.setter
    def action_resolution(self, v: str):
        self._action_resolution = ActionResolutionType(v)


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
