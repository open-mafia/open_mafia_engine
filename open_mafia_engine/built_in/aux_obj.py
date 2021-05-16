from __future__ import annotations
from typing import List
from open_mafia_engine.core import AuxGameObject, Game, Event, EPostPhaseChange


class KeyAux(AuxGameObject):
    """Aux object that can be created by key."""

    def __init__(self, key: str):
        self.key = key

    @classmethod
    def get_or_create(cls, game: Game, key: str, **kwargs) -> KeyAux:
        found: List[KeyAux] = game.aux.filter_by_type(cls)
        found = [x for x in found if x.key == key]
        if len(found) == 0:
            res = game.aux.add(cls(key=key, **kwargs))
        elif len(found) == 1:
            res = found[0]
            for k, v in kwargs.items():
                setattr(res, k, v)
        else:
            raise ValueError(f"Multiple KeyAux with same key found: {key!r}")
        return res


class IntKeyAux(KeyAux):
    """Aux object that holds a key and integer value."""

    def __init__(self, key: str, value: int = 0):
        self.key = key
        self.value = int(value)

    @property
    def value(self) -> int:
        return self._value

    @value.setter
    def value(self, v: int):
        self._value = int(v)


class IntPerPhaseKeyAux(IntKeyAux):
    """IntKeyAux that resets every new phase."""

    def __subscribe__(self, game: Game) -> None:
        game.add_sub(self, EPostPhaseChange)

    def __unsubscribe__(self, game: Game) -> None:
        game.remove_sub(self, EPostPhaseChange)

    def respond_to_event(self, event: Event, game: Game) -> None:
        if isinstance(event, EPostPhaseChange):
            self.value = 0
