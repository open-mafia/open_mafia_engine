"""

"""

import typing
import inspect
from mafia.util import ReprMixin, name_of, intersect
from mafia.core.errors import AmbiguousName
from mafia.core.event import Subscriber, EventManager
from mafia.core.ability import (
    Ability,
    AbilityAlreadyBound,
    ActivatedAbility,
    TryActivateAbility,
)
from mafia.state.access import Accessor, AccessError
from mafia.state.status import Status
from mafia.api.base import AccessAPI, SubStatusAPI


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

    class AlignmentAPI(AccessAPI):
        """API for alignments.
    
        Attributes
        ----------
        _parent : Alignment
            The parent alignment.
        access_levels : list
            List of access levels for this API instance.
        """

        def __init__(
            self, _parent: "Alignment", access_levels: typing.List[str] = ["public"]
        ):
            super().__init__(_parent=_parent, access_levels=access_levels)

        def get_actor_names(self) -> typing.List[str]:
            """Returns sorted list of actor (player) names for this Alignment.
            
            Required levels: [alignment.name]

            TODO
            ----
            Add alignments that let you see other members. Maybe a flag?...
            """
            al_name = name_of(self._parent)
            if al_name not in self.access_levels:
                raise AccessError(required=[al_name], given=self.access_levels)
            return sorted(name_of(a) for a in self._parent.members)

        def get_actor_api(self, name: str) -> "Actor.ActorAPI":
            """Gets API for actor with a particular name.
            
            Raises
            ------
            KeyError
                If no such actor has that name.
            """
            actor = self._parent.get_actor_by_name(name)
            return actor.api

    @property
    def api(self) -> "Alignment.AlignmentAPI":
        return self.AlignmentAPI(_parent=self)

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

    class ActorAPI(SubStatusAPI):
        """API for actors.
        
        Attributes
        ----------
        _parent : Actor
            The parent Actor.    
        access_levels : list
            List of access levels for this API instance.
    """

        def __init__(
            self, _parent: "Actor", access_levels: typing.List[str] = ["public"]
        ):
            super().__init__(_parent=_parent, access_levels=access_levels)

        def get_alignment_names(self) -> typing.List[str]:
            """Returns sorted list of alignment names for this Actor.
            
            Required levels: [actor.name]

            TODO
            ----
            Maybe allow co-members to see subset of alignments?...
            """
            required = [name_of(self._parent)]
            if not intersect(required, self.access_levels):
                raise AccessError(required=required, given=self.access_levels)
            return sorted(name_of(a) for a in self._parent.alignments)

        def get_alignment_api(self, name: str) -> Alignment.AlignmentAPI:
            """Gets API for own alignment with a particular name.
            
            Raises
            ------
            KeyError
                If no such alignment (for this actor) has that name.
            """
            actor = self._parent.get_alignment_by_name(name)
            return actor.api

        def _abil_dict(self, abil: Ability) -> typing.Dict[str, object]:
            """Creates ability description dict. Helper function.
            
            TODO
            ----
            Move this to Ability class, maybe?
            """
            res = {}
            if isinstance(abil, ActivatedAbility):
                sig = inspect.signature(abil.activate)
                res["activated"] = True
                res["signature"] = str(sig)
                res["parameters"] = list(sig.parameters)  # param names
            else:
                res["activated"] = False
            res["type"] = str(type(abil))
            # TODO: Add end-user description instead of docstring
            res["docstring"] = abil.__doc__
            return res

        def get_ability_info_all(self) -> typing.Dict[str, typing.Dict[str, object]]:
            """Returns map of ability names to information for this Actor.
            
            Required levels: [actor.name]
            """
            required = [name_of(self._parent)]
            if not intersect(required, self.access_levels):
                raise AccessError(required=required, given=self.access_levels)
            res = {}
            for abil in self._parent.abilities:
                res[name_of(abil)] = self._abil_dict(abil)
            return res

        def get_ability_names(self) -> typing.List[str]:
            """Returns list of ability names.
            
            Required levels: [actor.name]
            """
            return list(self.get_ability_info_all())

        def get_ability_info(self, ability_name: str) -> typing.Dict[str, object]:
            """Gets information for the given ability."""
            abil = self._parent.get_ability_by_name(ability_name)
            return self._abil_dict(abil)

        def use_activated_ability(
            self, game: EventManager, ability_name: str, **kwargs
        ):
            """Uses an activated ability given the keyword arguments.

            Parameters
            ----------
            game : Game
                The current Game, required for searching for arguments.
            ability_name : str
                The name of the ability you want to use.
            kwargs : dict
                Keyword arguments for the activated ability.
                Note that string arguments are attempted to be converted to 
                first player names, then alignment names. If those fail, then 
                we fall back to using the string representation.

            Notes
            -----
            Problems that had to be solved:
            
            * How do you send extra information (e.g. a target) without actually 
              sending an Actor object? (Answer: search for it by name.)
            
            * How do you actually execute the action? 
              (Answer: :meth:`game.handle_event`)
            """
            abil = self._parent.get_ability_by_name(ability_name)
            if not isinstance(abil, ActivatedAbility):
                raise TypeError("Ability is not an activated ability.")

            # Create new keyword arguments
            new_kw = {}
            for key, val in kwargs.items():
                if isinstance(val, str):
                    # search for actor or alignment with the given name
                    try:
                        actor = game.get_actor_by_name(val)
                        val = actor
                    except KeyError:
                        try:
                            align = game.get_alignment_by_name(val)
                            val = align
                        except KeyError:
                            val = val
                new_kw[key] = val

            # Create and handle event with new kwargs
            tae = TryActivateAbility(abil, **new_kw)
            game.handle_event(tae)

    @property
    def api(self) -> "Actor.ActorAPI":
        return self.ActorAPI(_parent=self)

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
