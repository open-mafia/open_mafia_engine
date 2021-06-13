from __future__ import annotations

import inspect
import logging
from abc import ABCMeta
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    DefaultDict,
    Dict,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from makefun import wraps

from open_mafia_engine.errors import MafiaAmbiguousTypeName, MafiaConverterError
from open_mafia_engine.util.classes import class_name
from open_mafia_engine.util.repr import ReprMixin

if TYPE_CHECKING:
    from open_mafia_engine.core.game import Game

NoneType = type(None)

logger = logging.getLogger(__name__)

__abstract_types__: Dict[str, Type[GameObject]] = {}
__concrete_types__: Dict[str, Type[GameObject]] = {}


class _BAD_HINT(object):
    """Sentinel for a bad type hint."""


def _get_ns() -> dict:
    from open_mafia_engine.core.all import Game

    res = locals()
    res.update(__concrete_types__)
    res.update(__abstract_types__)
    res["Game"] = Game
    return res


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
            logger.info(str(MafiaAmbiguousTypeName(cls, existing)))
            # raise MafiaAmbiguousTypeName(cls, existing)
            # NOTE: This + generated abilities + pickling = nightmare...
            # I guess we can assume generated abilities are the same? :)
            return existing  # just return the existing class!
        if inspect.isabstract(cls):
            __abstract_types__[cn] = cls
        else:
            __concrete_types__[cn] = cls
        return cls


class _Converter(object):
    """Global converter object."""

    def __init__(self):
        self._map: DefaultDict[
            Type[GameObject], Dict[Type, Callable[[Game, Any], GameObject]]
        ] = defaultdict(dict)

    def register(self, func: Callable) -> Callable:
        """Register this function as a converter."""

        sig = inspect.signature(func)
        type_hints = get_type_hints(func)

        params = list(sig.parameters.values())
        try:
            p_game, p_arg = params
        except Exception:
            raise TypeError(f"Expected exactly 2 arguments, but got signature: {sig!r}")

        # Check that we have everything
        try:
            return_type = type_hints["return"]
            arg_type = type_hints[p_arg.name]
            # game_type = type_hints[p_game.name]
        except KeyError as e:
            raise TypeError(f"converter() requires type annotations!") from e
        if not issubclass(return_type, GameObject):
            raise TypeError(f"Only converters for `GameObject` are allowed.")

        # Using defaultdict
        self._map[return_type][arg_type] = func

        return func

    def can_convert_to(self, type_: Type) -> bool:
        """Whether we can theoretically convert to `type_`."""

        if type_ is None:
            return True

        _t_origin = get_origin(type_)
        _t_args = get_args(type_)

        if _t_origin is Union:
            return all(self.can_convert_to(x) for x in _t_args)
        elif _t_origin is not None:
            return False

        try:
            if issubclass(type_, GameObject):
                return True
        except Exception:
            # For example, if `type_` is a Typing object...
            return False

        return False

    def convert(
        self,
        game: Game,
        type_: Union[NoneType, Type[GameObject]],
        obj: Optional[Any],
    ) -> Optional[GameObject]:
        """Convert `obj` to the given `type_`, in the context of the `game`."""

        if (type_ is None) or (type_ is NoneType):
            if obj is None:
                return None
            raise TypeError(f"obj must be None, got {obj!r}")

        if isinstance(obj, type_):  # also works if None, NoneType :)
            return obj

        _t_origin = get_origin(type_)
        _t_args = get_args(type_)

        if _t_origin is Union:  # Union or Optional
            for arg in _t_args:
                try:
                    return self.convert(game, arg, obj)
                except Exception:
                    pass
            # We went through all args - couldn't convert.
            raise MafiaConverterError(obj, type_)
        elif _t_origin is not None:
            raise TypeError(f"{_t_origin!r} is not supported for conversion.")

        # Find the function - try direct match, or using first subclass that works
        func_map = self._map[type_]
        func = func_map.get(type(obj))
        if func is not None:
            return func(game, obj)
        for t, f in func_map.items():
            if isinstance(obj, t):
                try:
                    return f(game, obj)
                except Exception:
                    logger.exception(f"Couldn't convert using {f!r}, trying again.")
        raise MafiaConverterError(obj, type_)


converter = _Converter()


def inject_converters(func: Callable) -> Callable:
    """Decorator that adds converters for all possible types."""

    if hasattr(func, "__is_converting__"):
        return func

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Work with signature
        sig = inspect.signature(func)
        sb = sig.bind(*args, **kwargs)
        sb.apply_defaults()  # we want to convert the default,s too!
        # Get type hints
        # FIXME: Unsure whether this will work for external subclasses.
        type_hints = get_type_hints(func, localns=_get_ns())

        game_param = sig.parameters.get("game")

        if game_param is None:
            self_param = sig.parameters.get("self")
            if self_param is None:
                raise TypeError(f"`game` or `self` are required, got {sig!r}")
            self: GameObject = sb.arguments["self"]
            if not isinstance(self, GameObject):
                raise TypeError(f"`self` must be GameObject, got {self!r}")
            game: Game = self.game
        else:
            game: Game = sb.arguments["game"]
        params = list(sig.parameters.values())

        nargs = []
        nkw = {}
        for p in params:
            val = sb.arguments[p.name]
            if p.kind == inspect.Parameter.VAR_POSITIONAL:
                # TODO: special behavior for sequence of params
                # e.g. f(game, *actors: List[Actor])
                nargs.extend(val)
            elif p.kind == inspect.Parameter.VAR_KEYWORD:
                # TODO: special behavior for mapping of params
                # e.g. f(game, **maps: Dict[str, Actor])
                nkw.update(val)
            else:
                th = type_hints.get(p.name, _BAD_HINT)
                if converter.can_convert_to(th):
                    val = converter.convert(game, th, val)
                    # except MafiaConverterError:
                    #     # TODO: Pre-check instead?
                    #     pass

                if p.kind == inspect.Parameter.POSITIONAL_ONLY:
                    nargs.append(val)
                elif p.name in sb.kwargs:
                    nkw[p.name] = val
                else:
                    nargs.append(val)

        res = func(*nargs, **nkw)
        return res

    setattr(wrapper, "__is_converting__", True)  # FIXME
    return wrapper


class GameObject(ReprMixin, metaclass=GameObjectMeta):
    """Base class for game objects."""

    def __init__(self, game, /):
        from open_mafia_engine.core.game import Game

        if not isinstance(game, Game):
            raise TypeError(f"Expected Game, got {game!r}")
        self._game = game
        game.add(self)

    @property
    def game(self) -> Game:
        return self._game
