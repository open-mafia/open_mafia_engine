from enum import Enum
from typing import List, Type


def make_str_enum(name: str, values: List[str], doc: str = "") -> Type[str]:
    """Makes a string enumeration with particuluar values."""

    T = Enum(name, {v: v for v in values}, qualname=name, type=str)

    def __repr__(self: T) -> str:
        cn = type(self).__qualname__
        return f"{cn}({self.value!r})"

    T.__repr__ = __repr__
    T.__doc__ = doc

    return T
