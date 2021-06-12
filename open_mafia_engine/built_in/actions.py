from open_mafia_engine.core.all import Action, Actor, Game, GameObject

from .auxiliary import RoleBlockerAux


class DeathCausingAction(Action):
    """Action that causes an Actor to die.

    Note that KillAction and LynchAction, which are subclasses, are not subclasses
    of each other. This is to differentiate "kills" and "lynches" and other action
    types that cause death.
    """

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        target: Actor,
        *,
        priority: float = 0.0,
        canceled: bool = False,
    ):
        self._target = target
        super().__init__(game, source, priority=priority, canceled=canceled)

    @property
    def target(self) -> Actor:
        return self._target

    @target.setter
    def target(self, v: Actor):
        self._target = v

    def doit(self):
        self.target.status["dead"] = True


class KillAction(DeathCausingAction):
    """Action that kills the target."""


class LynchAction(DeathCausingAction):
    """Action that lynches the target."""


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
        self._target = target
        super().__init__(game, source, priority=priority, canceled=canceled)

    @property
    def target(self) -> Actor:
        return self._target

    def doit(self):
        RoleBlockerAux(self.game, target=self.target, only_abilities=True)
