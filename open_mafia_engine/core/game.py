from __future__ import annotations

from pathlib import Path
from typing import Callable, IO, List, Optional, Union

import cloudpickle

from open_mafia_engine.core.auxiliary import AuxHelper, AuxObject
from open_mafia_engine.core.enums import ActionResolutionType
from open_mafia_engine.core.event_system import Action, ActionQueue, Event, EventEngine
from open_mafia_engine.core.game_object import GameObject
from open_mafia_engine.core.phase_cycle import (
    AbstractPhaseSystem,
    ETryPhaseChange,
    Phase,
    PhaseChangeAction,
    SimplePhaseCycle,
)
from open_mafia_engine.core.state import Actor, Faction


class Game(object):
    """Defines the state of an entire game, including the execution context.

    Parameters
    ----------
    gen_phases : Callable[[Game], AbstractPhaseSystem]
        A function that creates a phase system, given a Game.
        Use `AbstractPhaseSystem.gen(*args, **kwargs)` to create this function.
        The default is `SimplePhaseCycle.gen()`, which creates a day-night cycle.

    Attributes
    ----------
    event_engine : EventEngine
        The event engine, which handles all subscription and broadcasting.
    action_queue : ActionQueue
        The base action queue, which holds all core-level actions & all history.
    phase_system : AbstractPhaseSystem
        System that defines phases and their transitions.
    actors : List[Actor]
        All the actors (players) of the game.
    factions : List[Faction]
        All the factions (teams) of the game.
    aux : AuxHelper
        Helper object for auxiliary game objects.
    """

    def __init__(
        self,
        gen_phases: Callable[[Game], AbstractPhaseSystem] = SimplePhaseCycle.gen(),
    ):
        self._event_engine = EventEngine(self)
        self._action_queue = ActionQueue(self)
        self._actors: List[Actor] = []
        self._factions: List[Faction] = []
        self._phase_system: AbstractPhaseSystem = gen_phases(self)
        self._aux = AuxHelper(self)

    def __repr__(self):
        cn = type(self).__qualname__
        return f"{cn}()"

    @property
    def event_engine(self) -> EventEngine:
        return self._event_engine

    @property
    def action_queue(self) -> ActionQueue:
        return self._action_queue

    @property
    def actors(self) -> List[Actor]:
        return list(self._actors)

    @property
    def actor_names(self) -> List[str]:
        return [x.name for x in self._actors]

    @property
    def factions(self) -> List[Faction]:
        return list(self._factions)

    @property
    def faction_names(self) -> List[str]:
        return [x.name for x in self._factions]

    @property
    def phase_system(self) -> AbstractPhaseSystem:
        return self._phase_system

    @property
    def current_phase(self) -> Phase:
        return self.phase_system.current_phase

    @property
    def aux(self) -> AuxHelper:
        return self._aux

    def add(self, obj: GameObject):
        """Adds the object to this game.

        This is automatically called during `obj.__init__()`
        """
        if isinstance(obj, Actor):
            if obj not in self._actors:
                self._actors.append(obj)
        elif isinstance(obj, Faction):
            if obj not in self._factions:
                self._factions.append(obj)
        elif isinstance(obj, AuxObject):
            self._aux.add(obj)
        # NOTE: We ignore all other objects, but don't throw.

    # TODO: remove()?

    def process_event(self, event: Event, *, process_now: bool = False):
        """Processes the action."""
        responses: List[Action] = self.event_engine.broadcast(event)
        for resp in responses:
            self.action_queue.enqueue(resp)

        process_now = (
            process_now
            or self.current_phase.action_resolution == ActionResolutionType.instant
            or isinstance(event, ETryPhaseChange)
        )
        if process_now:
            self.action_queue.process_all()

    def change_phase(self, new_phase: Optional[Phase] = None):
        """Changes the phase to the given one (or bumps it). This causes events."""
        # NOTE: You can pass strings here, because ETryPhaseChange.__init__ converts
        self.process_event(ETryPhaseChange(self, new_phase=new_phase))
        # `process_now=True` is implicit :)

    def save(self, file: Union[Path, str, IO[bytes]]):
        """Cloudpickle-based saving"""
        if isinstance(file, Path):
            with file.open(mode="wb") as f:
                self.save(f)
        elif isinstance(file, str):
            return self.save(Path(file))
        else:
            cloudpickle.dump(self, file)

    @classmethod
    def load(cls, file: Union[Path, str, IO[bytes]]) -> Game:
        """Cloudpickle-based loading"""

        if isinstance(file, Path):
            with file.open(mode="rb") as f:
                return cls.load(f)
        elif isinstance(file, str):
            return cls.load(Path(file))
        else:
            res = cloudpickle.load(file)
            if not isinstance(res, cls):
                raise TypeError(f"Wrong object was pickled: {file!r}")
            return res