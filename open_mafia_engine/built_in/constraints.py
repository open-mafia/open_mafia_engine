"""Built-in ability constraints."""

from typing import Any, Dict, List, Optional
from open_mafia_engine.core import (
    CancelAction,
    Event,
    Ability,
    Constraint,
    Game,
    EPreAction,
)
from .aux_obj import IntPerPhaseKeyAux


class PhaseConstraint(Constraint):
    """Action can only be used during specific phases."""

    def __init__(self, parent: Ability, phase_names: List[str]):
        super().__init__(parent)
        self._phase_names = phase_names

    @property
    def phase_names(self) -> List[str]:
        return self._phase_names

    def is_ok(self, game: Game, **params: Dict[str, Any]) -> bool:
        return game.phases.current.name in self.phase_names


class DayConstraint(PhaseConstraint):
    """Action can only be used during the 'day' phase."""

    def __init__(self, parent: Ability):
        super().__init__(parent, phase_names=["day"])


class NightConstraint(PhaseConstraint):
    """Action can only be used during the 'night' phase."""

    def __init__(self, parent: Ability):
        super().__init__(parent, phase_names=["night"])


class ActorAliveConstraint(Constraint):
    """Action can only be used while alive."""

    def __init__(self, parent: Ability):
        super().__init__(parent)

    def is_ok(self, game: Game, **params: Dict[str, Any]) -> bool:
        return not self.parent.owner.status["dead"]


class KeywordActionLimitPerPhaseConstraint(Constraint):
    """Limited actions per phase, for abilities that share this keyword."""

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
    """Limited actions per phase, for abilities of this particular actor."""

    def __init__(self, parent: Ability, n_actions: int = 1):
        super().__init__(
            parent,
            keyword=f"actor_action_limit_per_phase:{parent.owner.name}",
            n_actions=n_actions,
        )
