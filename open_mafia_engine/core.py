from __future__ import annotations
from enum import Enum
from typing import List, Tuple, Union
from open_mafia_engine.util.repr import ReprMixin


class Alignment(ReprMixin):
    """A 'team' of Actors.

    Attributes
    ----------
    name : str
    actors : List[Actor]

    TODO: Add wincons.
    """

    def __init__(self, name: str, actors: List[Actor] = None):
        if actors is None:
            actors = []
        self.name = name
        self._actors = list(actors)

    def add_actor(self, actor: Actor):
        if actor not in self._actors:
            self._actors.append(actor)
            actor.add_alignment(self)

    def remove_actor(self, actor: Actor):
        if actor in self._actors:
            self._actors.remove(actor)
            actor.remove_alignment(self)

    @property
    def actors(self) -> List[Actor]:
        return list(self._actors)


class Actor(ReprMixin):
    """Represents a person or character.

    Attributes
    ----------
    name : str
    alignments : List[Alignment]
    abilities : List[Ability]
    """

    def __init__(
        self,
        name: str,
        alignments: List[Alignment] = None,
        abilities: List[Ability] = None,
    ):
        if abilities is None:
            abilities = []
        if alignments is None:
            alignments = []
        self.name = name

        # "parent" alignment
        self._alignments = list(alignments)
        for al in self._alignments:
            al.add_actor(self)

        self._abilities = list(abilities)

    @property
    def alignments(self) -> List[Alignment]:
        return list(self._alignments)

    @alignments.setter
    def alignments(self, new_alignments: List[Alignment]):
        """Changing alignments - remove self from old ones, add to new ones."""
        to_del = [a for a in self._alignments if a not in new_alignments]
        to_add = [a for a in new_alignments if a not in self._alignments]
        for al in to_del:
            al.remove_actor(self)
        for al in to_add:
            al.add_actor(self)
        self._alignments = list(new_alignments)  # technically not needed

    def add_alignment(self, al: Alignment):
        if al not in self._alignments:
            self._alignments.append(al)
            al.add_actor(self)

    def remove_alignment(self, al: Alignment):
        if al in self._alignments:
            self._alignments.remove(al)
            al.remove_actor(self)

    @property
    def abilities(self) -> List[Ability]:
        return list(self._abilities)

    def remove_ability(self, ability: Ability):
        """Removes the ability entirely."""
        if ability in self._abilities:
            self._abilities.remove(ability)
            del ability

    def take_control_of_ability(self, ability: Ability):
        """Moves the ability to this owner."""
        if ability not in self._abilities:
            ability.owner = self


class Ability(ReprMixin):
    """

    Attributes
    ----------
    name : str
    owner : Actor
        Abilities must always have an owner that points back at them.
    constraints : List[Constraint]
        Constraints on ability usage.
    """

    def __init__(self, name: str, owner: Actor, constraints: List[Constraint] = None):
        if constraints is None:
            constraints = []
        self.name = name

        self._owner = owner
        self._owner._abilities.append(self)

        self._constraints = list(constraints)
        for c in constraints:
            self.take_control_of_constraint(c)

    def clone(self, new_owner: Actor) -> Ability:
        """Clones this ability with a new owner."""
        raise NotImplementedError("TODO: Implement")

    @property
    def owner(self) -> Actor:
        return self._owner

    @owner.setter
    def owner(self, new_owner: Actor):
        """Changing owner - should remove self from the old one."""
        self._owner._abilities.remove(self)
        self._owner = new_owner
        self._owner._abilities.append(self)

    @property
    def constraints(self) -> List[Constraint]:
        return list(self._constraints)

    def remove_constraint(self, constraint: Constraint):
        if constraint in self._constraints:
            self._constraints.remove(constraint)
            del constraint

    def take_control_of_constraint(self, constraint: Constraint):
        if constraint not in self._constraints:
            constraint.parent = self


class ActivatedAbility(Ability):
    # TODO: trigger by some UseAbility event?
    pass


class Constraint(ReprMixin):
    def __init__(self, parent: Ability):
        self._parent = parent
        self._parent._constraints.append(self)

    @property
    def parent(self) -> Ability:
        return self._parent

    @parent.setter
    def parent(self, new_parent: Ability):
        """Changing parent."""
        self._parent._constraints.remove(self)
        self._parent = new_parent
        self._parent._constraints.append(self)


class ActionResolutionType(str, Enum):
    """When actions are resolved."""

    instant = "instant"
    end_of_phase = "end_of_phase"


class Phase(ReprMixin):
    """Represents a monolithic "phase" of action.

    Attributes
    ----------
    name : str
        The current phase name.
    action_resolution : ActionResolutionType
        One of {"instant", "end_of_phase"}
    """

    def __init__(self, name: str, action_resolution: Union[str, ActionResolutionType]):
        self.name = name
        self.action_resolution = ActionResolutionType(action_resolution)


class Game(ReprMixin):
    """Holds game state and logic.

    Attributes
    ----------
    game_actor : Actor
        The fake actor that represents the game's actions.
    current_phase : Phase
        Defines the current phase, including how actions are resolved.
    alignments : List[Alignment]
    actors : List[Actor]
    """

    def __init__(
        self,
        *,
        current_phase: Phase,
        game_actor: Actor,
        alignments: List[Alignment] = None,
        actors: List[Actor] = None,
    ):
        if alignments is None:
            alignments: List[Alignment] = []
        if actors is None:
            actors: List[Actor] = []
        # TODO: Maybe hide behind properties?
        # Probably only if we add backlinks.
        self.game_actor = game_actor
        self.current_phase = current_phase
        self.alignments = alignments
        self.actors = actors
