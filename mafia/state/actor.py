"""

"""

import typing
from mafia.util import ReprMixin, name_of
from mafia.core.errors import AmbiguousName
from mafia.core.event import Subscriber
from mafia.core.ability import Ability, AbilityAlreadyBound
from mafia.state.access import Accessor
from mafia.state.status import Status


import warnings


class Alignment(ReprMixin, Subscriber):
    """Represents an alignment (team).

    Attributes
    ----------
    name : str
        A human-readable name.
    members : list
        List of alignment members.
    victory : None or bool
        Whether the alignment has won. If None, this hasn't been determined yet.
        Default is None.
    """

    def __init__(
        self, name: str, members: list = [], victory: typing.Optional[bool] = None
    ):
        self.name = name
        self.members = list(members)
        self.victory = victory
        # Fake a subscription to get picked up by Game
        self.subscribe_to()

    def __str__(self):
        return self.name

    # add, remove
    def add(self, actor):
        """Adds actor to this alignment.
        
        Parameters
        ----------
        actor : Actor
            The new member of the alignment.
        """
        if not isinstance(actor, Actor):
            raise TypeError("Expected Actor, got %r" % actor)

        if actor in self.members:
            return

        self.members.append(actor)
        actor.alignments.append(self)

    def remove(self, actor):
        """Removes actor from this alignment.
        
        Parameters
        ----------
        actor : Actor
            The member that is leaving the alignment.
        """
        if not isinstance(actor, Actor):
            raise TypeError("Expected Actor, got %r" % actor)

        if actor not in self.members:
            return

        self.members.remove(actor)
        actor.alignments.remove(self)

    def get_actor_by_name(self, name: str) -> "Actor":
        """Gets the actor with the given name, in this alignment.
        
        Raises
        ------
        KeyError
            If no such actor (in this alignment) has that name.
        TODO
        ----
        Lower code duplication with :meth:`Game.get_actor_by_name`?
        """
        candidates = [a for a in self.members if name_of(a) == name]
        if len(candidates) == 0:
            raise KeyError(f"Actor with name '{name}' not found.")
        elif len(candidates) > 1:
            warnings.warn(
                AmbiguousName(
                    f"Multiple candidates found for name '{name}': {candidates}"
                )
            )
        return candidates[0]


class ActorStatus(Status):
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
        super().__init__(alive=alive, **kwargs)


class Actor(Accessor, Subscriber):
    """Represents an actor (player, NPC, etc.).
    
    Parameters
    ----------
    name : str
        Human-readable name.
    alignments : list
        Linked alignments.
    abilities : list
        Abilities, both activated and triggered.
    status : ActorStatus
        Dotted-dict for status information. 
    
    Attributes
    ----------
    access_levels : list
        List of all access levels available for this actor.
    """

    def __init__(
        self,
        name: str,
        alignments: typing.List[Alignment] = [],
        abilities: typing.List[Ability] = [],
        status: typing.Mapping[str, object] = ActorStatus(),
    ):
        self.name = name

        # Associate alignments (add self to them - if already there, it's safe)
        self.alignments = []
        for align in alignments:
            align.add(self)

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

        self.status = ActorStatus(**status)

        # Fake a subscription to be auto-added to a Game
        self.subscribe_to()

    def __str__(self):
        return self.name

    @property
    def access_levels(self) -> typing.List[str]:
        """Access levels."""
        return ["public", self.name] + [a.name for a in self.alignments]

    def get_alignment_by_name(self, name: str) -> Alignment:
        """Gets the alignment with the given name, for this Actor.
        
        Raises
        ------
        KeyError
            If no such alignment (for this actor) has that name.

        TODO
        ----
        Lower code duplication with :meth:`Game.get_alignment_by_name`?
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

    def get_ability_by_name(self, name: str) -> Ability:
        """Gets the ability with the given name, for this Actor.
        
        Raises
        ------
        KeyError
            If no such ability (for this actor) has that name.
        """
        candidates = [a for a in self.abilities if name_of(a) == name]
        if len(candidates) == 0:
            raise KeyError(f"Ability with name '{name}' not found.")
        elif len(candidates) > 1:
            warnings.warn(
                AmbiguousName(
                    f"Multiple candidates found for name '{name}': {candidates}"
                )
            )
        return candidates[0]


class Moderator(Actor):
    """Represents a moderator (game master, admin).

    Currently this is just an Actor. 
    Mods can be players too, theoretically...
    
    Parameters
    ----------
    name : str
        Human-readable name.
    alignments : list
        Linked alignments.
    abilities : list
        Abilities, both activated and triggered.
    status : ActorStatus
        Dotted-dict for status information. 
    
    Attributes
    ----------
    access_levels : list
        List of all access levels available for this actor.
    """
