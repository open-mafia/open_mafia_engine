from __future__ import annotations

from typing import Any, Dict, MutableMapping, TYPE_CHECKING, List

from open_mafia_engine.core.game_object import GameObject, inject_converters
from open_mafia_engine.core.event_system import Event, Subscriber

# from open_mafia_engine.core.outcome import Outcome, OutcomeAction

if TYPE_CHECKING:
    from open_mafia_engine.core.game import Game


class Faction(GameObject):
    """Faction, a.k.a. Alignment."""

    def __init__(self, game: Game, /, name: str):
        self.name = name
        self._actors: List[Actor] = []
        self._outcome_checkers: List[OutcomeChecker] = []
        super().__init__(game)

    @property
    def actors(self) -> List[Actor]:
        return list(self._actors)

    @property
    def actor_names(self) -> List[str]:
        return [x.name for x in self._actors]

    @property
    def outcome_checkers(self) -> List[OutcomeChecker]:
        return list(self._outcome_checkers)

    @inject_converters
    def add_actor(self, actor: Actor):
        if not isinstance(actor, Actor):
            raise TypeError(f"Expected Actor, got {actor!r}")
        if actor in self._actors:
            return
        self._actors.append(actor)
        actor._factions.append(self)

    @inject_converters
    def remove_actor(self, actor: Actor):
        if actor in self._actors:
            self._actors.remove(actor)
        if self in actor._factions:
            actor._factions.remove(self)

    def add_outcome_checker(self, oc: OutcomeChecker):
        if not isinstance(oc, OutcomeChecker):
            raise TypeError(f"Expected OutcomeChecker, got {oc!r}")
        if oc in self._outcome_checkers:
            return
        self._outcome_checkers.append(oc)
        oc.parent = self

    # def remove_outcome_checker(self, oc: OutcomeChecker):
    #     if oc in self._outcome_checkers:
    #         self._outcome_checkers.remove(self)
    #         # Wait, what do we do with `oc._parent`?!


class OutcomeChecker(Subscriber):
    """Checks for Faction Outcome. Base class."""

    def __init__(self, game: Game, parent: Faction, /):
        super().__init__(game)
        self._parent = parent
        parent.add_outcome_checker(self)

    @property
    def parent(self) -> Faction:
        return self._parent


class Actor(GameObject):
    """Actor object."""

    def __init__(self, game: Game, /, name: str, status: Dict[str, Any] = None):
        if status is None:
            status = {}
        self.name = name
        self._abilities: List[Ability] = []
        self._factions: List[Faction] = []
        self._status: Status = Status(game, self, **status)
        super().__init__(game)

    @property
    def status(self) -> Status:
        return self._status

    @property
    def abilities(self) -> List[Ability]:
        return list(self._abilities)

    @property
    def factions(self) -> List[Faction]:
        return list(self._factions)

    def add_ability(self, ability: Ability):
        """Adds this ability to self, possibly removing the old owner."""
        if not isinstance(ability, Ability):
            raise TypeError(f"Expected Ability, got {ability!r}")
        if ability in self._abilities:
            return
        self._abilities.append(ability)
        if ability._owner is not self:
            ability._owner._abilities.remove(ability)
            ability._owner = self


class Ability(GameObject):
    """Basic Ability object."""

    def __init__(self, game: Game, /, owner: Actor):
        if not isinstance(owner, Actor):
            raise TypeError(f"Expected Actor, got {owner!r}")

        self._owner = owner
        super().__init__(game)
        owner.add_ability(self)

    @property
    def owner(self) -> Actor:
        return self._owner


class Status(GameObject, MutableMapping):
    """dict-like representation of an actor's status.

    Access of empty attribs gives None.
    Changing an attribute emits an EStatusChange event.

    Attributes
    ----------
    parent: Actor
    attribs : dict
        Raw keyword arguments for the status.
    """

    def __init__(self, game, /, parent: Actor, **attribs: Dict[str, Any]):
        super().__init__(game)
        self._parent = parent
        self._attribs = attribs

    @property
    def parent(self) -> Actor:
        return self._parent

    @property
    def attribs(self) -> Dict[str, Any]:
        return dict(self._attribs)

    def __getitem__(self, key) -> Any:
        return self._attribs.get(key, None)

    def __delitem__(self, key) -> None:
        old_val = self[key]
        if old_val is not None:
            del self._attribs[key]
        if old_val is None:  # TODO: Maybe broadcast always?
            return
        self.game.process_event(
            EStatusChange(self.game, self.parent, key, old_val, None)
        )

    def __setitem__(self, key, value) -> None:
        old_val = self[key]
        self._attribs[key] = value
        if old_val == value:  # TODO: Maybe broadcast always?
            return
        self.game.process_event(
            EStatusChange(self.game, self.parent, key, old_val, value)
        )

    def __len__(self) -> int:
        return len(self._attribs)

    def __iter__(self):
        return iter(self._attribs)

    def __repr__(self):
        cn = type(self).__qualname__
        parts = [repr(self.game), repr(self.parent)]
        for k, v in self._attribs.items():
            parts.append(f"{k}={v!r}")
        return f"{cn}(" + ", ".join(parts) + ")"


class EStatusChange(Event):
    """The Status has changed for some Actor."""

    def __init__(self, game, /, actor: Actor, key: str, old_val: Any, new_val: Any):
        super().__init__(game)
        self._actor = actor
        self._key = key
        self._old_val = old_val
        self._new_val = new_val

    @property
    def actor(self) -> Actor:
        return self._actor

    @property
    def status(self) -> Status:
        return self._actor.status

    @property
    def key(self) -> str:
        return self._key

    @property
    def old_val(self) -> Any:
        return self._old_val

    @property
    def new_val(self) -> Any:
        return self._new_val
