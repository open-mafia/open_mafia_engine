from __future__ import annotations

import inspect
from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, Protocol, Tuple, Type, TypeVar

from open_mafia_engine.errors import MafiaAmbiguousTypeName
from open_mafia_engine.util.classes import class_name
from open_mafia_engine.util.repr import ReprMixin

__abstract_types__: Dict[str, Type[GameObject]] = {}
__concrete_types__: Dict[str, Type[GameObject]] = {}


class GameObjectMeta(ABCMeta):
    """Metaclass for game objects."""

    def __new__(mcs, name, bases, namespace, **kwargs):
        global __abstract_types__
        global __concrete_types__

        # Modify the class as needed
        nsp = dict(namespace)
        if "__init__" in nsp:
            nsp["__init__"] = inject_converters(nsp["__init__"])

        cls = super().__new__(mcs, name, bases, nsp, **kwargs)

        # Add class to types
        cn = class_name(cls)
        existing = __abstract_types__.get(cn, __concrete_types__.get(cn))
        if existing is not None:
            raise MafiaAmbiguousTypeName(existing, cls)
        if inspect.isabstract(cls):
            __abstract_types__[cn] = cls
        else:
            __concrete_types__[cn] = cls
        return cls


class GameObject(ReprMixin, metaclass=GameObjectMeta):
    """Base class for game objects."""


def inject_converters(method: Callable) -> Callable:
    """Adds converters for all possible types."""

    if hasattr(method, "__converters__"):
        return method

    # sig = inspect.signature(method)
    # # TODO: Implement!
    # print(f"Adding converters for method: {method}")
    # print(f"Signature: {sig!r}")

    res = method
    setattr(res, "__converters__", True)  # FIXME
    return res
