from open_mafia_engine.core.all import Ability, Action, Actor, Game, GameObject


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


KillAbility = Ability.generate(
    KillAction,
    params=["target"],
    name="KillAbility",
    doc="Ability to perform kills",
    desc="Kills the target.",
)


class LynchAction(DeathCausingAction):
    """Action that lynches the target."""
