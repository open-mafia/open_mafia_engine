from typing import List, Optional

from open_mafia_engine.core.all import (
    Ability,
    Action,
    GameObject,
    Actor,
    ATBase,
    CancelAction,
    EPreAction,
    Game,
    handler,
)

from .auxiliary import TempPhaseAux
from .kills import KillAction


class KillProtectorAux(TempPhaseAux):
    """Aux object that protects the target from kills."""

    def __init__(
        self,
        game: Game,
        /,
        target: Actor,
        key: str = None,
        *,
        use_default_constraints: bool = True,
    ):
        self._target = target
        super().__init__(
            game, key=None, use_default_constraints=use_default_constraints
        )

    @property
    def target(self) -> Actor:
        return self._target

    @handler
    def handle_to_save(self, event: EPreAction) -> Optional[List[CancelAction]]:
        """Cancels the action if it came from the target."""

        if isinstance(event, EPreAction) and isinstance(event.action, KillAction):
            src = event.action.source
            if isinstance(src, ATBase):
                if self.only_abilities and not isinstance(src, Ability):
                    # Skip
                    return
                if src.owner == self.target:
                    return [CancelAction(self.game, self, target=event.action)]


class KillProtectAction(Action):
    """Action that protects the tarte from kills until the end of the phase."""

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        target: Actor,
        *,
        priority: float = 90,
        canceled: bool = False,
    ):
        self._target = target
        super().__init__(game, source, priority=priority, canceled=canceled)

    @property
    def target(self) -> Actor:
        return self._target

    def doit(self):
        KillProtectorAux(self.game, target=self.target)
