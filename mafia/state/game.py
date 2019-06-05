"""

"""

# TODO: Everything.
import typing
from mafia.util import ReprMixin

# from mafia.core.errors import MafiaError
from mafia.core.event import EventManager, Subscriber
from mafia.core.ability import Action, ActivatedAbility
from mafia.state.status import Status
from mafia.state.actor import Alignment, Actor
from mafia.state.access import Accessor


class PhaseChangeAction(Action):
    """Action that changes phases.
    
    Attributes
    ----------
    phase_state : PhaseState
        The target state that will be changed.
    new_phase : int or None
        The phase being changed to. If None, signifies next phase.
    canceled : bool
        Whether the action is canceled. Default is False.
    """

    def __init__(
        self,
        phase_state,
        new_phase: typing.Optional[int] = None,
        canceled: bool = False,
    ):
        if not isinstance(phase_state, PhaseState):
            raise TypeError("Expected PhaseState, got %r" % phase_state)
        super().__init__(canceled=canceled)
        self.phase_state = phase_state
        self.new_phase = new_phase

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

        if self.new_phase is None:
            self.phase_state.current = (self.phase_state.current + 1) % len(
                self.phase_state.states
            )
        else:
            self.phase_state.current = self.new_phase
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

    def __init__(self, name: str, owner=None, phase_state=None):
        if not isinstance(phase_state, PhaseState):
            raise TypeError("phase_state should be a PhaseState, got %r" % phase_state)
        super().__init__(name=name, owner=owner)
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
        return True

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
        super().__init__(phase=phase, **kwargs)


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

    @property
    def access_levels(self) -> typing.List[str]:
        """Access levels of all the actors and alignments."""
        res = ["public", "game"]
        for a in self.actors + self.alignments:
            res.extend(set(a.access_levels).difference(res))
        return res
