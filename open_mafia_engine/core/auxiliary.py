from __future__ import annotations

from typing import List

from open_mafia_engine.core.event_system import (
    Action,
    ActionQueue,
    Event,
    EventEngine,
    Subscriber,
)
from open_mafia_engine.core.game_object import GameObject


class AuxObject(Subscriber):
    """Base class for auxiliary objects."""


class AuxHelper(GameObject):
    """Auxiliary object helper."""

    def __init__(self, game, /, max_objects: int = 1000):
        self._children: List[AuxObject] = []
        self._max_objects = int(max_objects)
        super().__init__(game)

    @property
    def max_objects(self) -> int:
        return self._max_objects

    @property
    def children(self) -> List[AuxObject]:
        return list(self._children)

    def add(self, obj: AuxObject):
        if not isinstance(obj, AuxObject):
            raise TypeError(f"Expected AuxObject, got {obj!r}")
        if obj not in self._children:
            self._children.append(obj)

    # TODO - remove
