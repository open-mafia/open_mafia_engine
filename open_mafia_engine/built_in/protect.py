from typing import List, Optional

from open_mafia_engine.core.all import (
    Ability,
    Action,
    Actor,
    ATBase,
    ConditionalCancelAction,
    EPreAction,
    Game,
    GameObject,
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
    def handle_to_save(
        self, event: EPreAction
    ) -> Optional[List[ConditionalCancelAction]]:
        """Cancels the action if it came from the target."""

        if isinstance(event, EPreAction) and isinstance(event.action, KillAction):
            # NOTE: This will protect only our target from kills, even if this
            # kill is redirected somewhere.

            def cond(action: KillAction) -> bool:
                """Cancel only if the final target is self."""
                return action.target == self.target

            return [
                ConditionalCancelAction(
                    self.game, self, target=event.action, condition=cond
                )
            ]


class KillProtectAction(Action):
    """Action that protects the tarte from kills until the end of the phase."""

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        target: Actor,
        *,
        priority: float = 80,
        canceled: bool = False,
    ):
        self._target = target
        super().__init__(game, source, priority=priority, canceled=canceled)

    @property
    def target(self) -> Actor:
        return self._target

    def doit(self):
        KillProtectorAux(self.game, target=self.target)


KillProtectAbility = Ability.generate(
    KillProtectAction,
    params=["target"],
    name="KillProtectAbility",
    doc="Ability to protect from kills",
    desc="Protects the target from kills.",
)
