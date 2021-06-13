from __future__ import annotations

from typing import Callable, Dict, List

from open_mafia_engine.core.game import Game
from open_mafia_engine.errors import MafiaBadBuilder
from open_mafia_engine.util.matcher import FuzzyMatcher
from open_mafia_engine.util.repr import ReprMixin

_GameBuilderFunc = Callable[..., Game]  # This signature is not quite enough.

__builders__: Dict[str, _GameBuilderFunc] = {}


def _assert_game_builder(func: Callable):
    """Raises an exception if not a game builder."""

    if not callable(func):
        raise MafiaBadBuilder(func)

    # TODO: Implement! Inspect the resulting signature?


class GameBuilder(ReprMixin):
    """Specification for a Game Builder.

    TODO: Allow lazy loading of specs, somehow.
    """

    def __init__(self, func: _GameBuilderFunc, /, name: str):
        global __builders__

        _assert_game_builder(func)
        self._func = func
        self._name = name

        __builders__[name] = self

    def build(self, player_names: List[str], *args, **kwargs) -> Game:
        """Builds the game based on passed players and other options."""
        return self.func(player_names, *args, **kwargs)

    @property
    def func(self) -> _GameBuilderFunc:
        return self._func

    @property
    def name(self) -> str:
        return self._name

    @classmethod
    def load(cls, name: str) -> GameBuilder:
        """Load a spec by exact or closest name."""
        global __builders__
        matcher = FuzzyMatcher(__builders__, score_cutoff=10)
        return matcher[name]

    @classmethod
    def available(cls) -> List[str]:
        """Returns the names of available builders."""
        global __builders__
        return list(__builders__.keys())


def game_builder(name: str = None) -> Callable[[_GameBuilderFunc], _GameBuilderFunc]:
    """Decorator factor for game builders."""

    def inner(func: _GameBuilderFunc) -> _GameBuilderFunc:
        nonlocal name

        if name is None:
            name = func.__qualname__
        GameBuilder(func, name=name)

        return func

    return inner
