from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Mapping, Type, Union, get_args, get_origin
from uuid import uuid4

from open_mafia_engine.core.event_system import (
    Action,
    ActionQueue,
    Event,
    EventEngine,
    Subscriber,
)
from open_mafia_engine.core.game_object import GameObject

if TYPE_CHECKING:
    from open_mafia_engine.core.game import Game

NoneType = type(None)


class AuxObject(Subscriber):
    """Base class for auxiliary objects.

    Aux objects have a key they are retrievable by.

    Attributes
    ----------
    game : Game
    key : str
        The key to retrieve the object by. If None (default), generates one.
    """

    def __init__(
        self, game: Game, /, key: str = None, *, use_default_constraints: bool = True
    ):
        if key is None:
            key = self.generate_key()
        self._key = str(key)
        # NOTE: super().__init__ auto-adds self to the AuxHelper
        super().__init__(game, use_default_constraints=use_default_constraints)

    @classmethod
    def generate_key(cls) -> str:
        """Generates a key for this class (used if None is passed in __init__)."""
        return cls.__qualname__ + "_" + str(uuid4()).replace("-", "")

    @property
    def key(self) -> str:
        return self._key

    @classmethod
    def get_or_create(
        cls,
        game: Game,
        /,
        key: str = None,
        *,
        use_default_constraints: bool = True,
        **kwargs,
    ) -> AuxObject:
        """Finds the AuxObject by key or, if there is no object, creates it."""
        if key is None:
            key = cls.generate_key()
        res = game.aux.get(key)
        if res is None:
            res = cls(
                game, key=key, use_default_constraints=use_default_constraints, **kwargs
            )
        if not isinstance(res, cls):
            raise TypeError(f"Wrong type for AuxObject: expected {cls!r}, got {res!r}")
        return res


class AuxHelper(GameObject, Mapping):
    """Auxiliary object helper."""

    def __init__(self, game, /, max_objects: int = 1000):
        self._key_map: Dict[str, AuxObject] = {}
        # self._children: List[AuxObject] = []
        self._max_objects = int(max_objects)
        super().__init__(game)

    @property
    def max_objects(self) -> int:
        return self._max_objects

    @property
    def children(self) -> List[AuxObject]:
        return list(self._key_map.values())

    def __getitem__(self, key: str):
        return self._key_map[key]

    def __iter__(self):
        return iter(self._key_map)

    def __len__(self):
        return len(self._key_map)

    def add(self, obj: AuxObject):
        """Adds the aux object to self."""
        if not isinstance(obj, AuxObject):
            raise TypeError(f"Expected AuxObject, got {obj!r}")
        if self._key_map.get(obj.key) == obj:
            return
        elif obj.key in self._key_map.keys():
            # FIXME: different object with the same key!
            return
        elif obj in self._key_map.values():
            # FIXME: same object with different key? Key should be able to change.
            return
        # OK, let's add it
        if len(self) > self.max_objects:
            raise ValueError(f"Reached {self.max_objects} (max) aux objects!")
        self._key_map[obj.key] = obj

    def remove(self, obj: AuxObject):
        """Removes `obj` from self."""
        if not isinstance(obj, AuxObject):
            raise TypeError(f"Expected AuxObject, got {obj!r}")
        found = self._key_map.get(obj.key)
        if found is None:
            return
        elif found == obj:
            del self._key_map[obj.key]
            obj._unsub()
        else:
            # FIXME: Object has different key, or another object has same key
            return

    def filter_by_type(self, T: Type[AuxObject]) -> List[AuxObject]:
        """Returns all `AuxObject`s with the given type.

        You can pass in Union types as well.
        """

        if get_origin(T) == Union:
            T_raw = get_args(T)
            T = tuple(x for x in T_raw if x is not None)
            # T is a tuple of types

        def chk(x):
            try:
                return isinstance(x, T)
            except Exception:
                return False

        return [x for x in self._key_map.values() if chk(x)]


class RemoveAuxAction(Action):
    """Removes the aux object, at the end of the stack."""

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        target: AuxObject,
        *,
        priority: float = -100,
        canceled: bool = False,
    ):
        self._target = target
        super().__init__(game, source, priority=priority, canceled=canceled)

    @property
    def target(self) -> AuxObject:
        return self._target

    def doit(self):
        self.game.aux.remove(self.target)
