from typing import List, Optional

from open_mafia_engine.core.all import (
    Ability,
    Action,
    Actor,
    ATBase,
    CancelAction,
    EPreAction,
    Game,
    GameObject,
    handler,
)

from .auxiliary import TempPhaseAux


class RoleBlockerAux(TempPhaseAux):
    """Aux object that blocks actions made by the target.

    It removes itself after the end of the phase.

    Attributes
    ----------
    game : Game
    target : Actor
        The target to block.
    key : None or str
        Safely ignore this (?).
    only_abilities : bool
        If True, only blocks Ability activations, and lets Triggers through.
        Default is True.
    """

    def __init__(
        self,
        game: Game,
        /,
        target: Actor,
        key: str = None,
        *,
        only_abilities: bool = True,
        use_default_constraints: bool = True,
    ):
        self._only_abilities = bool(only_abilities)
        self._target = target
        super().__init__(
            game, key=None, use_default_constraints=use_default_constraints
        )

    @property
    def target(self) -> Actor:
        return self._target

    @property
    def only_abilities(self) -> bool:
        return self._only_abilities

    @handler
    def handle_to_cancel(self, event: EPreAction) -> Optional[List[CancelAction]]:
        """Cancels the action if it came from the target."""
        if isinstance(event, EPreAction):
            src = event.action.source
            if isinstance(src, ATBase):
                if self.only_abilities and not isinstance(src, Ability):
                    # Skip
                    return
                if src.owner == self.target:
                    return [CancelAction(self.game, self, target=event.action)]


class RoleBlockAction(Action):
    """Action that prevents the target from actioning until the end of the phase."""

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
        self.target = target
        super().__init__(game, source, priority=priority, canceled=canceled)

    def doit(self):
        RoleBlockerAux(self.game, target=self.target, only_abilities=True)


RoleBlockAbility = Ability.generate(
    RoleBlockAction,
    params=["target"],
    name="RoleBlockAbility",
    doc="Ability to block others.",
    desc="Roleblocks the target.",
)
