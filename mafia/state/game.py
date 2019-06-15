"""

"""

import typing
import logging

from mafia.util import ReprMixin, name_of
from mafia.core.errors import AmbiguousName
from mafia.core.event import EventManager, Subscriber, Event, Action
from mafia.core.ability import ActivatedAbility, Restriction
from mafia.state.status import Status
from mafia.state.actor import Alignment, Actor
from mafia.state.access import Accessor, AccessError
from mafia.api.base import AccessAPI

import warnings


class PhaseChangeAction(Action):
    """Action that changes phases.
    
    Attributes
    ----------
    phase_state : PhaseState
        The target state that will be changed.
    new_phase : int or str or None
        The phase being changed to. If None, signifies next phase.
    canceled : bool
        Whether the action is canceled. Default is False.
    """

    def __init__(
        self,
        phase_state,
        new_phase: typing.Optional[typing.Union[int, str]] = None,
        canceled: bool = False,
    ):
        if not isinstance(phase_state, PhaseState):
            raise TypeError("Expected PhaseState, got %r" % phase_state)
        super().__init__(canceled=canceled)

        if new_phase is None:
            self.new_phase = None
        elif isinstance(new_phase, int):
            self.new_phase = phase_state.states[new_phase]
        elif isinstance(new_phase, str):
            self.new_phase = new_phase
        else:
            raise TypeError(f"Expected int, str, or None, got {type(new_phase)}")
        self.phase_state = phase_state

    @classmethod
    def next_phase(cls, phase_state) -> Action:  # actually PhaseChangeAction
        """Creates action that increments the phase (with wrap-around).
        
        Parameters
        ----------
        phase_state : PhaseState
            The target state that will be changed.
        """
        return cls(phase_state, None)

    def __execute__(self) -> bool:
        if self.canceled:
            return False

        np = self.new_phase

        if np is None:
            self.phase_state.current_index = (self.phase_state.current_index + 1) % len(
                self.phase_state.states
            )
        elif isinstance(np, str):
            self.phase_state.current = np
        elif isinstance(np, int):
            self.phase_state.current_index = np
        return True


class PhaseChangeAbility(ActivatedAbility):
    """Ability to change phases. Usually just given to the moderator.
    
    Attributes
    ----------
    name : str
        Ability name (human-readable).
    owner : object
        The object that owns the ability.
    phase_state : PhaseState
        The phase object that this ability allows changing.
    """

    def __init__(
        self,
        name: str,
        owner=None,
        restrictions: typing.List[Restriction] = [],
        phase_state=None,
    ):
        if not isinstance(phase_state, PhaseState):
            raise TypeError("phase_state should be a PhaseState, got %r" % phase_state)
        super().__init__(name=name, owner=owner, restrictions=restrictions)
        self.phase_state = phase_state

    def is_legal(self, new_phase: typing.Optional[int] = None) -> bool:
        """Check whether the phase change ability usage is legal.

        The constructor prevents using phase change on a non-phase-state. 
        You may want to override/extend this with stricter checks. 

        Parameters
        ----------
        new_phase : int or None
            The index of the phase you want. If None, just takes next phase.

        Returns
        -------
        can_use : bool
            Whether the ability usage is legal.
        """
        return super().is_legal(new_phase=new_phase)

    def activate(self, new_phase: typing.Optional[int] = None) -> PhaseChangeAction:
        """Creates a PhaseChangeAction.
        
        If the activation is illegal, it will raise 
        an :class:`IllegalAbilityActivation` error.

        Parameters
        ----------
        new_phase : int or None
            The index of the phase you want. If None, just takes next phase.

        Returns
        -------
        action : Action or None
            Resulting Action to put on the queue.

        Raises
        ------
        IllegalAbilityActivation
            If not `self.is_legal`.
        """
        super().activate(new_phase=new_phase)

        if new_phase is None:
            return PhaseChangeAction.next_phase(self.phase_state)

        return PhaseChangeAction(phase_state=self.phase_state, new_phase=new_phase)


class PhaseState(ReprMixin):
    """Specifies current "phase" of the game state and progression.
    
    Attributes
    ----------
    states : list
        List of phase names. Defaults to `['day', 'night']`.
    current_index : int
        Index of current phase. Defaults to 0. 
    current : str
        The current phase. Property.
    """

    def __init__(self, states=["day", "night"], current_index=0):
        states = list(states)
        self.current_index = current_index % len(states)
        self.states = states

    @property
    def current(self):
        return self.states[self.current_index]

    @current.setter
    def current(self, new_phase: typing.Union[str, int]):
        if isinstance(new_phase, int):
            self.current_index = new_phase % len(self.states)
        elif isinstance(new_phase, str):
            try:
                idx = [i for i, k in enumerate(self.states) if k == new_phase][0]
            except IndexError:
                raise KeyError(f"No phase {repr(new_phase)} found in {self.states}.")
            self.current_index = idx
        else:
            raise TypeError("Bad phase type passed, expected int or str.")

    class PhaseStateAPI(AccessAPI):
        """API for a PhaseState."""

        def __init__(
            self, _parent: "PhaseState", access_levels: typing.List[str] = ["public"]
        ):
            super().__init__(_parent=_parent, access_levels=access_levels)

        def get_current_phase_name(self) -> str:
            """Returns current phase name.
            
            Required access levels: None
            """
            return self._parent.current

        def get_all_phase_names(self) -> typing.List[str]:
            """Returns all possible phase names in list, sorted by internal order.
            
            Required access levels: None
            """
            return list(str(s) for s in self._parent.states)

    @property
    def api(self) -> "PhaseState.PhaseStateAPI":
        return self.PhaseStateAPI(_parent=self)

    def __str__(self):
        return f"{self.current} (of {self.states})"

    def __next__(self) -> PhaseChangeAction:
        return self.try_change_phase()

    def try_change_phase(self, new_phase: int = None) -> PhaseChangeAction:
        """Attempts to change phase to new one.
        
        Parameters
        ----------
        new_phase : int or None
            The new phase. If None, tries to increment. 

        Returns
        -------
        action : PhaseChangeAction
            The actual action that changes the phase.
        """

        if new_phase is None:
            action = PhaseChangeAction.next_phase(self)
        else:
            action = PhaseChangeAction(self, new_phase)
        return action


class GameStatus(Status):
    """Status of an Game.

    This acts like a mutable dotted-dict, however it isn't recursive 
    (not meant to be) and it stores values as :class:`StatusItem`'s.
    
    Parameters
    ----------
    phase : PhaseState
        The current phase, cycle, etc.
    finished : bool
        Whether the game has completed. Default is False.
    kwargs : dict
        Keyword arguments to set.
    """

    def __init__(
        self, phase: PhaseState = PhaseState(), finished: bool = False, **kwargs
    ):
        super().__init__(phase=phase, finished=finished, **kwargs)


class GameFinished(Event):
    """Signal that the game has ended.
    
    Attributes
    ----------
    game : Game
        The game that has finished.
    """

    def __init__(self, game: EventManager):
        self.game = game


class GameEndAction(Action):
    """Ends the game, preventing actions from occuring after resolution.
    
    Attributes
    ----------
    game : Game
        The game to finish.
    canceled : bool
        Whether to cancel the game-ending action.
    """

    def __init__(self, game: EventManager, canceled: bool = False):
        super().__init__(canceled=canceled)
        self.game = game

    @property
    def priority(self) -> float:
        return float("-inf")

    def __execute__(self) -> bool:
        if self.canceled:
            return False

        # Force pre-game-end checks
        self.game.handle_event(GameFinished(self.game))

        # Create message
        result_lines = "\n".join(
            [
                f" - {name_of(al)} : {'won' if al.victory else 'lost'}"
                for al in self.game.alignments
            ]
        )
        logging.getLogger(__name__).info("Game finished. Results:\n" + result_lines)

        # Set game as finished
        # (though, theoretically, some may have not won or lost...)
        self.game.status.finished = True
        return True


class Game(EventManager, Subscriber, Accessor):
    """Represents an entire game.

    This class works as an :class:`EventManager` and also as 
    a collection of :class:`Actor`'s and :class:`Alignment`'s.

    Use as a context manager to automatically pick up objects 
    within the context. This works for Actors, Alignments, and 
    also Moderators.
    
    Parameters
    ----------
    actors : list
        All actors in the game.
    alignments : list
        All alignments in the game.
    status : GameStatus
        Dotted-dict for status information. 
    
    Attributes
    ----------
    listeners : dict
        Dictionary of listeners for events (from EventManager).
    access_levels : list
        List of all access levels available for this actor.
    """

    def __init__(
        self,
        actors: typing.List[Actor] = [],
        alignments: typing.List[Alignment] = [],
        status: typing.Mapping[str, object] = GameStatus(),
    ):

        EventManager.__init__(self)

        # Just remember these in the game
        # Note that they are auto-added when subscribed
        self.actors = list(actors)
        self.alignments = list(alignments)

        # Game status
        self.status = GameStatus(**status)

    class GameAPI(AccessAPI):
        """API acess for a Game object."""

        def __init__(
            self, _parent: "Game", access_levels: typing.List[str] = ["public"]
        ):
            super().__init__(_parent=_parent, access_levels=access_levels)

        def get_alignment_names(self) -> typing.List[str]:
            """Returns sorted list of alignment names.
            
            Required levels: None
            """
            return sorted(name_of(a) for a in self._parent.alignments)

        def get_actor_names(self) -> typing.List[str]:
            """Returns sorted list of actor (player) names.
            
            Required levels: None
            """
            return sorted(name_of(a) for a in self._parent.actors)

        def start_game(self) -> None:
            """Starts the current game. Currently a no-op!
            
            Required levels: ['game']
            """
            if "game" not in self.access_levels:
                raise AccessError(required=["game"], given=self.access_levels)
            # TODO: Currently a No-Op

        def end_game(self) -> None:
            """Forcefully ends the current game. Currently a no-op!
            
            Required levels: ['game']
            """
            if "game" not in self.access_levels:
                raise AccessError(required=["game"], given=self.access_levels)
            # TODO: Currently a No-Op

        def get_status_keys(self) -> typing.List[str]:
            """Returns list of all accessible status keys.
            
            Required levels: (variable)
            """
            res = []
            sta = self._parent.status
            for key in sta.keys():
                try:
                    _ = sta[key].access(levels=self.access_levels)
                    res.append(key)
                except AccessError:
                    pass
            return res

        def get_status_value(self, key: str) -> object:
            """Returns object mapped to the 'key' string.
            
            Required levels: (variable)
            """
            obj = self._parent.status[key].access(levels=self.access_levels)
            return obj

        def get_status_api(self, key: str) -> AccessAPI:
            """Gets API for a particular key. 
            
            Raises
            ------
            AccessError
                If not enough access levels.
            AttributeError
                If object does not have an .api member.
            """
            obj = self._parent.status[key].access(levels=self.access_levels)
            return obj.api

    @property
    def api(self) -> "Game.GameAPI":
        return self.GameAPI(_parent=self)

    def get_actor_by_name(self, name: str) -> Actor:
        """Gets the actor with the given name.
        
        Raises
        ------
        KeyError
            If the actor was not found.
        """
        candidates = [a for a in self.actors if name_of(a) == name]
        if len(candidates) == 0:
            raise KeyError(f"Actor with name '{name}' not found.")
        elif len(candidates) > 1:
            warnings.warn(
                AmbiguousName(
                    f"Multiple candidates found for name '{name}': {candidates}"
                )
            )
        return candidates[0]

    def get_alignment_by_name(self, name: str) -> Alignment:
        """Gets the alignment with the given name.
        
        Raises
        ------
        KeyError
            If the alignment was not found.
        """
        candidates = [a for a in self.alignments if name_of(a) == name]
        if len(candidates) == 0:
            raise KeyError(f"Alignment with name '{name}' not found.")
        elif len(candidates) > 1:
            warnings.warn(
                AmbiguousName(
                    f"Multiple candidates found for name '{name}': {candidates}"
                )
            )
        return candidates[0]

    # EventManager overrides

    def subscribe_me(self, obj: Subscriber, *event_classes) -> None:
        """Subscribes `obj` to passed events.

        Also automaticallys picks up :class:`Actor`'s and 
        :class:`Alignment`'s and adds to own list.
        
        Parameters
        ----------
        obj : Subscriber
            Object to set as a subscriber.
        event_classes : list
            List of Event classes to subscribe to.
        """
        super().subscribe_me(obj, *event_classes)

        if isinstance(obj, Actor):
            self.actors.append(obj)
        elif isinstance(obj, Alignment):
            self.alignments.append(obj)

    def handle_event(self, event: Event) -> None:
        if self.status.finished.value:
            # No more events will be looked at
            return
        super().handle_event(event=event)

    # Accessor overrides

    @property
    def access_levels(self) -> typing.List[str]:
        """Access levels of all the actors and alignments."""
        res = ["public", "game"]
        for a in self.actors + self.alignments:
            res.extend(set(a.access_levels).difference(res))
        return res
