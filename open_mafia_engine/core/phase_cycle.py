from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Callable, Iterable, List, Optional, Tuple, Union

from open_mafia_engine.core.enums import ActionResolutionType
from open_mafia_engine.core.event_system import (
    Action,
    EPostAction,
    EPreAction,
    Event,
    Subscriber,
    handler,
)
from open_mafia_engine.core.game_object import GameObject, converter

if TYPE_CHECKING:
    from open_mafia_engine.core.game import Game


class Phase(GameObject):
    """Represents a monolithic "phase" of action.

    Attributes
    ----------
    name : str
        The current phase name.
    action_resolution : ActionResolutionType
        One of {"instant", "end_of_phase"}
    """

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

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Phase):
            return NotImplemented
        return (o.name == self.name) and (o.action_resolution == self.action_resolution)


class ETryPhaseChange(Event):
    """Try to change the phase."""

    def __init__(self, game, /, new_phase: Optional[Phase] = None):
        if not (new_phase is None or isinstance(new_phase, Phase)):
            new_phase = converter.convert(game, Phase, new_phase)
        self._new_phase = new_phase
        super().__init__(game)

    @property
    def new_phase(self) -> Optional[Phase]:
        return self._new_phase


class EPrePhaseChange(EPreAction):
    """Phase is about to change."""

    @property
    def action(self) -> PhaseChangeAction:
        return self._action

    @property
    def new_phase(self) -> Optional[Phase]:
        return self.action.new_phase

    @property
    def old_phase(self) -> Phase:
        return self.action.old_phase


class EPostPhaseChange(EPostAction):
    """Phase has changed."""

    @property
    def action(self) -> PhaseChangeAction:
        return self._action

    @property
    def new_phase(self) -> Optional[Phase]:
        return self.action.new_phase

    @property
    def old_phase(self) -> Phase:
        return self.action.old_phase


class PhaseChangeAction(Action):
    """Action to change the phase.

    Parameters
    ----------
    new_phase : None or Phase
        The resulting phase. By default, `None` uses the next phase.
    old_phase : Phase
        The phase that this action was created in.
    """

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        new_phase: Optional[Phase] = None,
        *,
        priority: float = 0.0,
        canceled: bool = False,
    ):
        super().__init__(game, source, priority=priority, canceled=canceled)
        self.new_phase = new_phase
        self._old_phase = self.game.current_phase

    @property
    def old_phase(self) -> Phase:
        return self._old_phase

    def doit(self):
        if self.new_phase is None:
            self.game.phase_system.bump_phase()
        else:
            self.game.phase_system.current_phase = self.new_phase

    Pre = EPrePhaseChange
    Post = EPostPhaseChange


class AbstractPhaseSystem(Subscriber):
    """Interface for a phase system.

    It's possible to see all phases by using `game.phase_system.possible_phases`
    """

    def __init__(self, game: Game, /, *, use_default_constraints: bool = True):
        super().__init__(game, use_default_constraints=use_default_constraints)
        self._startup = Phase(game, name="startup", action_resolution="instant")
        self._shutdown = Phase(game, name="shutdown", action_resolution="instant")

    @property
    def startup(self) -> Phase:
        return self._startup

    @property
    def shutdown(self) -> Phase:
        return self._shutdown

    @property
    @abstractmethod
    def possible_phases(self) -> Iterable[Phase]:
        """Returns all possible phases (as a new iterable).

        If it is infinite, override __getitem__ as well!
        """

    def __getitem__(self, key: str) -> Phase:
        """Returns the phase with the given name.

        By default, iterates over all possible phases.
        """
        if not isinstance(key, str):
            raise TypeError(f"Expected key as str, got {key!r}")
        for p in self.possible_phases:
            if key == p.name:
                return p
        raise KeyError(key)

    @property
    @abstractmethod
    def current_phase(self) -> Phase:
        """Returns the current phase."""

    @current_phase.setter
    @abstractmethod
    def current_phase(self, v: Phase):
        """Sets the current phase."""

    @abstractmethod
    def bump_phase(self) -> Phase:
        """Updates the phase to use the next one, then returns the current one."""

    @classmethod
    def gen(cls, *args, **kwargs) -> Callable[[Game], AbstractPhaseSystem]:
        """Create a callable that generates a phase cycle."""

        def func_gen(game: Game) -> AbstractPhaseSystem:
            return cls(game, *args, **kwargs)

        return func_gen

    @handler
    def system_phase_change(
        self, event: ETryPhaseChange
    ) -> Optional[List[PhaseChangeAction]]:
        """Some external system asked for a phase change."""
        if not isinstance(event, ETryPhaseChange):
            return
        return [PhaseChangeAction(self.game, self, event.new_phase)]


class SimplePhaseCycle(AbstractPhaseSystem):
    """Simple phase cycle definition.

    Parameters
    ----------
    game : Game
    cycle : None or List[Tuple[str, ActionResolutionType]]
        The cycle definition. Submit pairs of (name, resolution_type).
        By default, uses `[("day", "instant"), ("night", "end_of_phase")]`
    """

    _STARTUP = -1
    _SHUTDOWN = -2

    def __init__(
        self,
        game: Game,
        /,
        cycle: List[Tuple[str, ActionResolutionType]] = None,
        current_phase: Optional[str] = None,
    ):
        super().__init__(game)
        if cycle is None:
            cycle = [("day", "instant"), ("night", "end_of_phase")]
        cphases = []
        names = set()
        for name, ar in cycle:
            if name in names:
                raise ValueError(f"Duplicate name {name!r} in {names}")
            ar = ActionResolutionType(ar)
            names.add(name)
            cphases.append(Phase(game, name=name, action_resolution=ar))
        self._cycle = cphases
        self._i = self._STARTUP
        if current_phase is not None:
            self.current_phase = current_phase

    @property
    def cycle(self) -> List[Phase]:
        return list(self._cycle)

    @property
    def possible_phases(self) -> List[Phase]:
        return [self.startup, *self.cycle, self.shutdown]

    @property
    def current_phase(self) -> Phase:
        """Returns the current phase."""
        if self._i == self._STARTUP:
            return self.startup
        elif self._i == self._SHUTDOWN:
            return self.shutdown
        i = self._i % len(self._cycle)
        return self._cycle[i]

    @current_phase.setter
    def current_phase(self, v: Union[str, Phase]):
        if isinstance(v, str):
            new_phase = self[v]
        else:
            new_phase = v
        if new_phase == self.startup:
            # Maybe disallow going back to startup?
            self._i = self._STARTUP
        elif new_phase == self.shutdown:
            self._i = self._SHUTDOWN
        elif new_phase in self.possible_phases:
            # Just move through all phases implicitly - we won't trigger anything
            while self.current_phase != new_phase:
                self._i += 1
        else:
            raise ValueError(f"No such phase found: {v!r}")

    def bump_phase(self) -> Phase:
        """Updates the phase to use the next one, then returns the current one.

        Trying to bump on `shutdown` phase will raise an error.
        """
        if self._i == self._STARTUP:
            self._i = 0
            return self.current_phase
        elif self._i == self._SHUTDOWN:
            raise ValueError(f"Cannot bump shutdown phase: {self.shutdown}")
        self._i += 1
        return self.current_phase

    @classmethod
    def gen(
        cls,
        cycle: List[Tuple[str, ActionResolutionType]] = None,
        current_phase: Optional[str] = None,
    ) -> Callable[[Game], SimplePhaseCycle]:
        """Generator for a simple phase cycle."""
        return super().gen(cycle=cycle, current_phase=current_phase)
