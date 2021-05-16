import logging
import random
from collections import Counter
from typing import List, Optional, Type, Union

from open_mafia_engine.core import (
    Action,
    Ability,
    ActivatedAbility,
    Actor,
    AuxGameObject,
    GameObject,
    Game,
)

logger = logging.getLogger(__name__)


class AbstractVote(GameObject):
    """A basic Vote class, which allows voting for GameObjects.

    Attributes
    ----------
    source : Actor
        The source of this vote.
    """

    def __init__(self, source: Actor):
        self.source = source

    @property
    def source(self) -> Actor:
        """Whoever cast this vote."""
        return self._source

    @source.setter
    def source(self, v: Actor):
        if not isinstance(v, Actor):
            raise TypeError(f"Expected Actor, got {v!r}")
        self._source = v


class UnvoteAll(AbstractVote):
    """Symbolic class for unvoting."""


class VoteAgainstAll(AbstractVote):
    """Symbolic class for voting against all options (e.g. no-lynch)."""


class VoteForTargets(AbstractVote):
    """Vote for zero or more targets.

    TODO: targets = None or targets = [] is essentially the same as UnvoteAll.
    Maybe override __new__ to fixate that?...
    """

    def __init__(self, source: Actor, targets: List = None):
        super().__init__(source=source)
        self.targets = targets

    @property
    def targets(self) -> List:
        return list(self._targets)

    @targets.setter
    def targets(self, targets: List):
        self._targets = self._chk_targets(targets)

    def _chk_targets(self, targets: List = None):
        if targets is None:
            targets = []
        return list(targets)


_SimpleVote = Union[UnvoteAll, VoteAgainstAll, VoteForTargets]


class SimpleVoteTally(AuxGameObject):
    """Vote tally that only supports multi-voting."""

    def __init__(
        self,
        votes: List[_SimpleVote] = None,
        *,
        select_on_tie: bool = False,
        allow_unvotes: bool = True,
        allow_against_all: bool = True,
    ):
        self.select_on_tie = select_on_tie
        self.allow_against_all = allow_against_all
        self.allow_unvotes = allow_unvotes
        # This will trigger adding all the votes
        self.votes = votes

    @property
    def votes(self) -> List[AbstractVote]:
        return list(self._votes)

    @votes.setter
    def votes(self, votes: List[_SimpleVote]):
        self._votes: List[_SimpleVote] = []
        if votes is None:
            votes = []
        for v in votes:
            self.add(v)

    def _chk_vote(self, vote: _SimpleVote):
        if isinstance(vote, VoteAgainstAll):
            if not self.allow_against_all:
                raise ValueError(f"This tally does not allow VoteAgainstAll.")
        if isinstance(vote, UnvoteAll):
            if not self.allow_unvotes:
                raise ValueError(f"This tally does not allow unvoting.")

    def add(self, vote: _SimpleVote) -> None:
        """Adds a vote, removing all previous votes."""
        previous_votes = [v for v in self._votes if v.source == vote.source]
        for pv in previous_votes:
            self._votes.remove(pv)
        self._votes.append(vote)

    def clear(self) -> None:
        """Clears all votes."""
        self.votes = None

    @property
    def leaders(self) -> list:
        cnt = Counter()
        for vote in self._votes:
            if isinstance(vote, VoteAgainstAll):
                cnt.update([VoteAgainstAll])  # use as a sentinel type
            elif isinstance(vote, UnvoteAll):
                pass  # ignore
            elif isinstance(vote, VoteForTargets):
                targets = vote.targets
                cnt.update(targets)
            else:
                raise TypeError(f"Unexpected or unsupported type of vote: {vote!r}")
        # Short-circuit
        if len(cnt) == 0:
            return []
        # Select all leaders with the most votes
        top_votes = cnt.most_common(1)[0][1]
        res = [t for (t, c) in cnt.most_common() if c == top_votes]
        return res

    def select_leader(self) -> Optional[object]:
        """Selects a single vote leader (or None).

        If tied and `select_on_tie`, a random one will be chosen (otherwise, None).
        """
        leaders = self.leaders
        if len(leaders) == 0:
            return None
        elif len(leaders) == 1:
            return leaders[0]
        # len > 1
        if self.select_on_tie:
            logger.info(f"Selecting from leaders: {leaders}")
            return random.choice(leaders)
        return None


class VoteForActors(VoteForTargets):
    """Vote for zero or more actors."""

    @property
    def targets(self) -> List[Actor]:
        return list(self._targets)

    @targets.setter
    def targets(self, targets: List[Actor]):
        self._targets = self._chk_targets(targets)

    def _chk_targets(self, targets: List = None):
        targets = super()._chk_targets(targets)
        for t in targets:
            if not isinstance(t, Actor):
                raise TypeError(f"Expected Actor, got {t!r}")
        return targets


class VoteForActor(VoteForActors):
    """Vote for up to one actor."""

    def _chk_targets(self, targets: List[Actor] = None):
        targets = super()._chk_targets(targets)
        if len(targets) > 1:
            raise ValueError(f"Can vote for only 1 actor, but tried {len(targets)}.")
        return targets


class SimpleVoteAction(Action):
    """Casts a single vote on a tally."""

    def __init__(
        self,
        source: Ability,
        tally: Optional[SimpleVoteTally] = None,
        target: Union[None, object, Type[UnvoteAll]] = None,
        *,
        priority: float = 1.0,
        canceled: bool = False,
    ):
        super().__init__(source, priority=priority, canceled=canceled)
        self.target = target
        self.tally = tally

    def doit(self, game: Game) -> None:
        abil: Ability = self.source
        source: Actor = abil.owner
        if self.tally is None:
            tallies = game.aux.filter_by_type(SimpleVoteTally)
            if len(tallies) != 1:
                raise ValueError(f"Could not determine proper tally: {tallies}")
            tally: SimpleVoteTally = tallies[0]
        else:
            tally = self.tally
        if self.target is UnvoteAll:
            print(f"{source.name} unvoted.")  # FIXME: Remove
            tally.add(UnvoteAll(source=source))
        else:
            print(f"{source.name} voted for {self.target.name}!")  # FIXME: Remove
            tally.add(VoteForTargets(source=source, targets=[self.target]))
