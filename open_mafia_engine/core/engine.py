"""The core engine, to use as a context manager."""

from __future__ import annotations
from contextlib import AbstractContextManager
from typing import Optional


__engines__ = []


class MafiaEngine(AbstractContextManager):
    """Manages the game engine context."""

    def __init__(self):
        pass

    def __repr__(self) -> str:
        cn = type(self).__qualname__
        return f"{cn}()"

    def __enter__(self) -> MafiaEngine:
        global __engines__
        __engines__.append(self)
        return self

    def __exit__(self, exc_type=None, exc_value=None, tb=None) -> Optional[bool]:
        global __engines__
        if (len(__engines__) == 0) or (__engines__[-1] is not self):
            raise ValueError("Engine stack is corrupted!")
        __engines__.pop()
        return super().__exit__(exc_type, exc_value, tb)
