"""Built-in ability constraints."""

from typing import Any, Dict, List, Optional
import warnings

from open_mafia_engine.core import (
    Ability,
    Actor,
    CancelAction,
    Constraint,
    EPreAction,
    Event,
    Game,
)

from .aux_obj import IntPerPhaseKeyAux


class PhaseConstraint(Constraint):
    """Ability can only be used during specific phases."""

    def __init__(self, parent: Ability, phase_names: List[str]):
        super().__init__(parent)
        self._phase_names = phase_names

    @property
    def phase_names(self) -> List[str]:
        return self._phase_names

    def is_ok(self, game: Game, **params: Dict[str, Any]) -> bool:
        return game.phases.current.name in self.phase_names


class DayConstraint(PhaseConstraint):
    """Ability can only be used during the 'day' phase."""

    def __init__(self, parent: Ability):
        super().__init__(parent, phase_names=["day"])


class NightConstraint(PhaseConstraint):
    """Ability can only be used during the 'night' phase."""

    def __init__(self, parent: Ability):
        super().__init__(parent, phase_names=["night"])


class ActorAliveConstraint(Constraint):
    """Ability can only be used while alive."""

    def __init__(self, parent: Ability):
        super().__init__(parent)

    def is_ok(self, game: Game, **params: Dict[str, Any]) -> bool:
        return not self.parent.owner.status["dead"]


class TargetAliveConstraint(Constraint):
    """The target must be an Actor and alive when using the ability.

    Parameters
    ----------
    target_key : str = "target"
        The name of the argument for the constrained Action/Ability.
        The arg type should be Actor.
        Default is "target".

    NOTE: This currently doesn't check during the Action, only before Ability is used.
    """

    def __init__(self, parent: Ability, target_key: str = "target"):
        super().__init__(parent)
        self._target_key = str(target_key)

    @property
    def target_key(self) -> str:
        return self._target_key

    def is_ok(self, game: Game, **params: Dict[str, Any]) -> bool:
        if self.target_key not in params:
            raise ValueError(
                f"Improperly set `target_key`: {self.target_key!r} vs {list(params)}"
            )
        target = params[self.target_key]
        if isinstance(target, Actor):
            return not target.status["dead"]
        # raise TypeError(f"Target ({self.target_key}) must be Actor, got {target!r}")
        warnings.warn(f"Target ({self.target_key}) should be Actor, got {target!r}")
        return True


class KeywordActionLimitPerPhaseConstraint(Constraint):
    """Limited actions per phase, for all abilities that share this keyword."""

    def __init__(self, parent: Ability, keyword: str, n_actions: int = 1):
        super().__init__(parent)
        self.keyword = str(keyword)
        self.n_actions = int(n_actions)
        self._helper  # run get-or-create

    @property
    def _helper(self) -> IntPerPhaseKeyAux:
        return IntPerPhaseKeyAux.get_or_create(self.game, key=self.keyword)

    def is_ok(self, game: Game, **params: Dict[str, Any]) -> bool:
        """Preemptive check, to avoid making too many actions and canellations."""
        # TODO: Check if this is correct!
        return self._helper.value < self.n_actions

    # Make sure to increment the counter when we even try to use the action

    def __subscribe__(self, game: Game) -> None:
        game.add_sub(self, EPreAction)

    def __unsubscribe__(self, game: Game) -> None:
        game.remove_sub(self, EPreAction)

    def respond_to_event(self, event: Event, game: Game) -> Optional[CancelAction]:
        if isinstance(event, EPreAction):
            action = event.action
            if action.source is self.parent:
                if self._helper.value >= self.n_actions:
                    return CancelAction(source=self, target=action)
                self._helper.value += 1
        return None


class ActorActionLimitPerPhaseConstraint(KeywordActionLimitPerPhaseConstraint):
    """Limited actions per phase, for AALPPC abilities of this particular actor."""

    def __init__(self, parent: Ability, n_actions: int = 1):
        super().__init__(
            parent,
            keyword=f"actor_action_limit_per_phase:{parent.owner.name}",
            n_actions=n_actions,
        )
