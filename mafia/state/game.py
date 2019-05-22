"""

"""

# TODO: Everything.
import typing
from mafia.util import ReprMixin

# from mafia.core.errors import MafiaError
from mafia.core.event import Subscriber
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


class Game(ReprMixin, Subscriber):
    """Represents an actor (player, NPC, etc.).
    
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
    
    """

    def __init__(
        self,
        actors: typing.List[Actor] = [],
        alignments: typing.List[Alignment] = [],
        abilities: typing.List[Ability] = [],
        status: typing.Mapping[str, object] = {},
    ):
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
