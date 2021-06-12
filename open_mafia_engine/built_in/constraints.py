from typing import Optional

from open_mafia_engine.core.all import (
    Action,
    ATConstraint,
    AuxObject,
    Constraint,
    ConstraintActorTargetsAlive,
    ConstraintOwnerAlive,
    Game,
    SubscribedConstraint,
    Subscriber,
    PhaseChangeAction,
    handler,
)

from .auxiliary import CounterPerPhaseAux


class LimitPerPhaseKeyConstraint(SubscribedConstraint):
    """Allow only N uses per phase, given a key."""

    def __init__(self, game: Game, /, parent: Subscriber, key: str, limit: int = 1):
        self._key = str(key)
        self._limit = int(limit)
        super().__init__(game, parent)
        CounterPerPhaseAux.get_or_create(game, key=self._key)

    @property
    def key(self) -> str:
        return self._key

    @property
    def limit(self) -> int:
        return self._limit

    @property
    def counter(self) -> CounterPerPhaseAux:
        cppa = CounterPerPhaseAux.get_or_create(self.game, key=self._key)
        return cppa

    # TODO: How do we increment the counter?!
    # We need `Action.source`, don't we?...
    # Or we could subscribe to `EActivate` and check... not too cool, either.

    # self.counter.increment()

    def check(self, action: Action) -> Optional[Constraint.Violation]:
        v = self.counter.value
        if v >= self.limit:
            return self.Violation(
                f"Reached limit of {self.limit} (found {v}) for key {self.key!r}"
            )
