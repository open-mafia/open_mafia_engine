from typing import Optional
from open_mafia_engine.core import (
    Game,
    GameObject,
    Actor,
    Ability,
    ActivatedAbility,
    Action,
)


class KillAction(Action):
    """Kills the target."""

    def __init__(
        self,
        source: GameObject,
        target: Optional[Actor] = None,
        *,
        priority: float = 1.0,
        canceled: bool = False,
    ):
        super().__init__(source, priority=priority, canceled=canceled)
        self.target = target

    def doit(self, game: Game) -> None:
        src: Ability = self.source
        # victim = [x for x in game.actors if x.name == self.target][0]
        victim = self.target
        if victim is None:
            print(f"Nobody was killed by {src.owner.name}")  # FIXME: Remove
        else:
            victim: Actor
            victim.status["dead"] = True  # or 'alive' = False
            print(f"{src.owner.name} killed {victim.name}")  # FIXME: Remove


KillAbility = ActivatedAbility.create_type(KillAction, "KillAbility")

# TODO: Kill immunity, or doctor stuff, or...?
