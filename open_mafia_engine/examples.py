from open_mafia_engine.core import *


class VoteAction(Action):
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
        print(f"I voted for {self.target}!")


VoteAbility = ActivatedAbility.create_type(VoteAction, name="VoteAbility")
# VoteAbility = ActivatedAbility[VoteAction]  # alternate, but badly named


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


class Notifier(Subscriber):
    def __subscribe__(self, game: Game) -> None:
        game.add_sub(self, Event)

    def respond_to_event(self, event: Event, game: Game) -> Optional[Action]:
        print(f"  Saw event: {type(event).__qualname__}")
        return None
