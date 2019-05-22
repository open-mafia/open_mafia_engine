"""

"""

# TODO: Everything.
import typing
from mafia.util import ReprMixin

# from mafia.core.errors import MafiaError
from mafia.core.event import EventManager, Subscriber
from mafia.core.ability import Ability, AbilityAlreadyBound
from mafia.state.status import Status
from mafia.state.actor import Alignment, Actor


class GameStatus(Status):
    """Status of an Actor.

    This acts like a mutable dotted-dict, however it isn't recursive 
    (not meant to be) and it stores values as :class:`StatusItem`'s.
    
    Parameters
    ----------
    alive : bool
        Whether the actor is alive or not.
    kwargs : dict
        Keyword arguments to set.
    """

    def __init__(self, alive: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.alive = alive


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
        status: typing.Mapping[str, object] = {},
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

