from open_mafia_engine.core import *


class VoteAction(Action):
    """Fake vote for the target."""

    def __init__(
        self,
        source: GameObject,
        target: str = None,
        *,
        priority: float = 1.0,
        canceled: bool = False,
    ):
        super().__init__(source, priority=priority, canceled=canceled)
        self.target = target

    def doit(self, game: Game) -> None:
        src: Ability = self.source
        print(f"{src.owner.name} voted for {self.target}!")


VoteAbility = ActivatedAbility.create_type(VoteAction, name="VoteAbility")
# VoteAbility = ActivatedAbility[VoteAction]  # alternate, but badly named


class KillAction(Action):
    """Kills the target."""

    def __init__(
        self,
        source: GameObject,
        target: str = None,
        *,
        priority: float = 1.0,
        canceled: bool = False,
    ):
        super().__init__(source, priority=priority, canceled=canceled)
        self.target = target

    def doit(self, game: Game) -> None:
        src: Ability = self.source
        victim = [x for x in game.actors if x.name == self.target][0]
        victim.status["dead"] = True  # or 'alive' = False
        print(f"{src.owner.name} killed {self.target}")


KillAbility = ActivatedAbility[KillAction]


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


class AliveConstraint(Constraint):
    """Action can only be used while alive."""

    def __init__(self, parent: Ability):
        super().__init__(parent)

    def is_ok(self, game: Game, **params: Dict[str, Any]) -> bool:
        return not self.parent.owner.status["dead"]


class Notifier(Subscriber):
    def __subscribe__(self, game: Game) -> None:
        game.add_sub(self, Event)

    def respond_to_event(self, event: Event, game: Game) -> Optional[Action]:
        print(f"  EVENT: {type(event).__qualname__}")
        return None


class Mortician(Subscriber):
    def __subscribe__(self, game: Game) -> None:
        game.add_sub(self, EStatusChange)

    def respond_to_event(self, event: Event, game: Game) -> Optional[Action]:
        if isinstance(event, EStatusChange):
            if event.key == "dead":
                print(f"  DEATH of {event.actor.name}")
        return None
