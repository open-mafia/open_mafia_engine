from __future__ import annotations

from typing import Any, List, Optional

from open_mafia_engine.core.all import (
    Ability,
    Action,
    Actor,
    ATBase,
    AuxObject,
    CancelAction,
    EPreAction,
    EPostPhaseChange,
    Game,
    GameObject,
    PhaseChangeAction,
    RemoveAuxAction,
    handler,
)


class TempPhaseAux(AuxObject):
    """Aux object that removes itself after the phase."""

    @handler
    def remove_self(self, event: EPostPhaseChange) -> Optional[List[RemoveAuxAction]]:
        if isinstance(event, EPostPhaseChange):
            return [RemoveAuxAction(self.game, self, target=self)]


class ValueAux(AuxObject):
    """Aux object that represents a key-value pair."""

    def __init__(
        self,
        game: Game,
        /,
        key: str,
        value: Any,
        *,
        use_default_constraints: bool = True,
    ):
        super().__init__(game, key=key, use_default_constraints=use_default_constraints)
        self._value = self._fix_val(value)

    def _fix_val(self, v):
        """Fixes the value. Override this if needed."""
        return v

    @property
    def key(self) -> str:
        return self._key

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, v):
        # TODO: Event when value is changed?
        self._value = self._fix_val(v)

    @classmethod
    def get_or_create(cls, game: Game, /, key: str, value: Any, **kwargs) -> ValueAux:
        return super().get_or_create(game, key=key, value=value, **kwargs)


class CounterAux(ValueAux):
    """Int-valued aux object, with a default value of 0."""

    def __init__(
        self,
        game: Game,
        /,
        key: str,
        value: int = 0,
        *,
        use_default_constraints: bool = True,
    ):
        super().__init__(
            game, key=key, value=value, use_default_constraints=use_default_constraints
        )

    def _fix_val(self, v):
        return int(v)

    def increment(self):
        """Increments this counter by one (e.g. `self.value += 1`)"""
        self.value += 1

    @classmethod
    def get_or_create(
        cls, game: Game, /, key: str, value: int = 0, **kwargs
    ) -> CounterAux:
        return super().get_or_create(game, key=key, value=value, **kwargs)


class CounterPerPhaseAux(CounterAux):
    """CounterAux that resets after every phase ends."""

    @handler
    def reset_every_phase(self, event: EPostPhaseChange) -> None:
        if isinstance(event, EPostPhaseChange):
            self.value = 0
