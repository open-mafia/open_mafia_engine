from typing import Dict, List, Optional
from uuid import uuid4

from open_mafia_engine.core.all import (
    Action,
    ActionInspector,
    ATBase,
    ATConstraint,
    AuxObject,
    Constraint,
    ConstraintActorTargetsAlive,
    ConstraintOwnerAlive,
    Game,
    Phase,
    PhaseChangeAction,
    Subscriber,
    handler,
)
from open_mafia_engine.core.event_system import EPostAction, EPreAction
from open_mafia_engine.core.state import Actor

from .auxiliary import CounterPerPhaseAux


class PhaseConstraint(Constraint):
    """Allow only using in a particular phase."""

    def __init__(self, game, /, parent: Subscriber, phase: Phase):
        self._phase = phase
        super().__init__(game, parent)

    @property
    def phase(self) -> Phase:
        return self._phase

    def check(self, action: Action) -> Optional[Constraint.Violation]:
        cp = self.game.current_phase
        if cp != self.phase:
            return self.Violation(
                f"Wrong phase: currently {cp.name!r}, need {self.phase.name!r}."
            )


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


class ConstraintNoSelfTarget(ATConstraint):
    """Any targets for the action, if they are Actors, must not be the owner."""

    def check(self, action: Action) -> Optional[Constraint.Violation]:
        ai = ActionInspector(action)
        p2a: Dict[str, Actor] = ai.values_of_type(Actor)
        bads = []
        for p, a in p2a.items():
            if a == self.owner:
                bads.append(f"{p!r}")
        if len(bads) > 0:
            return self.Violation("Self-targeting not allowed: " + ", ".join(bads))


class ConstraintNoSelfFactionTarget(ATConstraint):
    """Any targets for the action, if they are Actors, must be from other factions."""

    def check(self, action: Action) -> Optional[Constraint.Violation]:
        ai = ActionInspector(action)
        p2a: Dict[str, Actor] = ai.values_of_type(Actor)
        bads = []
        for p, a in p2a.items():
            if any(f in self.owner.factions for f in a.factions):
                bads.append(f"{p!r} ({a.name!r})")
        s = "" if len(self.owner.factions) == 1 else "s"
        if len(bads) > 0:
            return self.Violation(f"Targets in own faction{s}: " + ", ".join(bads))
