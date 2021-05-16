"""Built-in ability constraints."""

from typing import Any, Dict, List
from open_mafia_engine.core import Ability, Constraint, Game


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

class AliveConstraint(Constraint):
    """Action can only be used while alive."""

    def __init__(self, parent: Ability):
        super().__init__(parent)

    def is_ok(self, game: Game, **params: Dict[str, Any]) -> bool:
        return not self.parent.owner.status["dead"]
