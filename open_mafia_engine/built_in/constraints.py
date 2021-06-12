from typing import List, Optional
from uuid import uuid4

from open_mafia_engine.core.all import (
    ATBase,
    Action,
    ATConstraint,
    AuxObject,
    Constraint,
    ConstraintActorTargetsAlive,
    ConstraintOwnerAlive,
    Game,
    Subscriber,
    PhaseChangeAction,
    handler,
)
from open_mafia_engine.core.event_system import EPostAction, EPreAction
from open_mafia_engine.core.state import Actor

from .auxiliary import CounterPerPhaseAux


class LimitPerPhaseKeyConstraint(Constraint):
    """Allow only N uses per phase, given a key.

    Attributes
    ----------
    game : Game
    parent : Subscriber
    key : str
        They key to use for the aux object.
    limit : int
        The maximum number of actions per phase. Default is 1.
    only_successful : bool
        Whether to count only successful tries towards the limit.
        Default is False (i.e. even attempts are counted).
    """

    def __init__(
        self,
        game: Game,
        /,
        parent: Subscriber,
        key: str = None,
        limit: int = 1,
        *,
        only_successful: bool = False,
    ):
        if key is None:
            key = self.generate_key(parent)
        self._key = key
        self._limit = int(limit)
        self._only_successful = bool(only_successful)
        super().__init__(game, parent)
        CounterPerPhaseAux.get_or_create(game, key=self._key)

    @classmethod
    def generate_key(cls, parent: Subscriber) -> str:
        cn = cls.__qualname__
        return f"{cn}_{uuid4()}".replace("-", "")

    @property
    def key(self) -> str:
        return self._key

    @property
    def limit(self) -> int:
        return self._limit

    @property
    def only_successful(self) -> bool:
        return self._only_successful

    @property
    def counter(self) -> CounterPerPhaseAux:
        cppa = CounterPerPhaseAux.get_or_create(self.game, key=self._key)
        return cppa

    def hook_pre_action(self, action: Action) -> Optional[List[Action]]:
        if not self.only_successful:
            self.counter.increment()

    def hook_post_action(self, action: Action) -> Optional[List[Action]]:
        if self.only_successful:
            self.counter.increment()

    # TODO: How do we increment the counter?!
    # We need `Action.source`, don't we?...
    # Or we could subscribe to `EActivate` and check... not too cool, either.
    # Plus it's incorrect for Triggers. Bah. I need to add `source`.

    # We also need to make sure additional triggers get canceled. Hmm.

    # self.counter.increment()

    def check(self, action: Action) -> Optional[Constraint.Violation]:
        v = self.counter.value
        if v >= self.limit:
            return self.Violation(
                f"Reached limit of {self.limit} (found {v}) for key {self.key!r}"
            )


class LimitPerPhaseActorConstraint(LimitPerPhaseKeyConstraint, ATConstraint):
    """Allow only N uses per phase for this actor.

    Attributes
    ----------
    game : Game
    parent : ATBase
    limit : int
        The maximum number of actions per phase. Default is 1.
    only_successful : bool
        Whether to count only successful tries towards the limit.
        Default is False (i.e. even attempts are counted).
    """

    def __init__(
        self,
        game: Game,
        /,
        parent: ATBase,
        limit: int = 1,
        *,
        only_successful: bool = False,
    ):
        key = self.generate_key(parent)
        super().__init__(
            game, parent, key, limit=limit, only_successful=only_successful
        )

    @classmethod
    def generate_key(cls, parent: ATBase) -> str:
        cn = cls.__qualname__
        return f"{cn}_{parent.owner.name}"

    @property
    def owner(self) -> Actor:
        return self.parent.owner

    # TODO: Same problem as with the base counter - how do we keep track of uses?
