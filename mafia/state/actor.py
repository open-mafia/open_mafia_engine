"""

"""

import typing

# from copy import deepcopy

from mafia.util import ReprMixin
from mafia.core.errors import MafiaError
from mafia.state.access import Accessor
from mafia.core.event import Subscriber
from mafia.core.ability import Ability


class Alignment(ReprMixin):
    """Represents an alignment (team).

    Attributes
    ----------
    name : str
        A human-readable name.
    members : list
        List of alignment members.
    """

    def __init__(self, name: str, members: list = []):
        self.name = name
        self.members = list(members)

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


class AbilityAlreadyBound(MafiaError):
    """Ability has already been bound to another owner."""

    def __init__(self, ability, new_owner):
        msg = "Cannot add owner %r to ability %r, already has owner." % (
            new_owner,
            ability,
        )
        super().__init__(msg)
        self.ability = ability
        self.new_owner = new_owner


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
    
    Attributes
    ----------
    access : list
        List of all access levels available for this actor.
    """

    def __init__(
        self,
        name: str,
        alignments: typing.List[Alignment] = [],
        abilities: typing.List[Ability] = [],
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

    @property
    def access(self) -> typing.List[str]:
        """Access levels."""
        return ["public", self.name] + [a.name for a in self.alignments]
