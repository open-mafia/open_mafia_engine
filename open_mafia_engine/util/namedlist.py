from collections.abc import Mapping, Sequence
from typing import List

from open_mafia_engine.util.repr import ReprMixin


class NamedList(Mapping, Sequence, ReprMixin):
    """Named list: works like a list and a dict based on the key."""

    def __init__(self, inner: List, attr: str = "name"):
        self._inner = list(inner)
        self._attrs = {getattr(o, attr): o for o in self._inner}
        self._attr = attr

    @property
    def inner(self) -> List:
        return self._inner

    @property
    def attr(self) -> str:
        return self._attr

    def __str__(self) -> str:
        return str(self._inner)

    def __getitem__(self, k):
        if isinstance(k, int):
            return self._inner[k]
        return self._attrs[k]

    def __len__(self) -> int:
        return len(self._inner)

    def __iter__(self):
        return iter(self._inner)