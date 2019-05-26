"""

"""

# TODO: Everything.
import typing
from mafia.util import ReprMixin

# from mafia.core.errors import MafiaError
from mafia.core.event import EventManager, Subscriber
from mafia.core.ability import Ability, AbilityAlreadyBound, Action
from mafia.state.status import Status
from mafia.state.actor import Alignment, Actor


class PhaseChangeAction(Action):
    """Action that changes phases.
    
    Attributes
    ----------
    phase_state : PhaseState
        The target state that will be changed.
    new_phase : int
        The phase being changed to.
    """

    def __init__(self, phase_state, new_phase: int):
        if not isinstance(phase_state, PhaseState):
            raise TypeError("Expected PhaseState, got %r" % phase_state)
        self.phase_state = phase_state
        self.new_phase = new_phase

    @classmethod
    def next_phase(cls, phase_state):
        """Creates action that increments the phase (with wrap-around).
        
        Parameters
        ----------
        phase_state : PhaseState
            The target state that will be changed.
        """
        new_phase = (phase_state.current + 1) % len(phase_state.states)
        return cls(phase_state, new_phase)

    def __execute__(self):
        self.phase_state.current = self.new_phase
        return True


class PhaseState(ReprMixin):
    """Specifies current "phase" of the game state and progression.
    
    Attributes
    ----------
    states : list
        List of phases. Defaults to `['day', 'night']`.
    current : int
        Index of current phase. Defaults to 0. 
    """

    def __init__(self, states=["day", "night"], current=0):
        states = list(states)
        self.current = current % len(states)
        self.states = states

    def __repr__(self):
        return "%s(states=%r, current=%r)" % (
            self.__class__.__name__,
            self.states,
            self.current,
        )

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
    kwargs : dict
        Keyword arguments to set.
    """

    def __init__(self, phase: PhaseState = PhaseState(), **kwargs):
        super().__init__(**kwargs)
        self.phase = phase


class Game(EventManager, ReprMixin, Subscriber):
    """Represents an entire game.

    This class works as an :class:`EventManager` and also as 
    a collection of :class:`Actor`'s and :class:`Alignment`'s.

    Use as a context manager to automatically pick up objects 
    within the context.
    
    Parameters
    ----------
    actors : list
        All actors in the game.
    alignments : list
        All alignments in the game.
    abilities : list
        Game-wide Abilities, both activated and triggered.
    status : GameStatus
        Dotted-dict for status information. 
    
    Attributes
    ----------
    listeners : dict
        Dictionary of listeners for events (from EventManager).
    """

    def __init__(
        self,
        actors: typing.List[Actor] = [],
        alignments: typing.List[Alignment] = [],
        abilities: typing.List[Ability] = [],
        status: typing.Mapping[str, object] = GameStatus(),
        # listeners: typing.Mapping[object, type] = {},
    ):

        EventManager.__init__(self)

        # Just remember these in the game
        self.actors = list(actors)
        self.alignments = list(alignments)

        # Associate abilities ()
        self.abilities = []
        for abil in abilities:
            if abil.owner is self:
                self.abilities.append(abil)
            elif abil.owner is None:
                # Take ownership :)
                abil.owner = self
                self.abilities.append(abil)
            else:
                raise AbilityAlreadyBound(abil, self)

        self.status = GameStatus(**status)

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
