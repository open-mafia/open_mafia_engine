from __future__ import annotations

from abc import abstractmethod
from collections import defaultdict
from typing import DefaultDict, Dict, List, Tuple, Union

from open_mafia_engine.core.api import (
    Ability,
    Action,
    Actor,
    AuxObject,
    Game,
    GameObject,
    converter,
    get_actor_by_name,
    inject_converters,
)

# TODO: tiebreaking enum, hammers, allow unvotes, allow against all


class AbstractVoteTarget(GameObject):
    """A target for voting. Don't use directly."""

    @abstractmethod
    def apply(self, vr: VotingResults, source: Actor):
        """Apply self on the voting results."""

    def __eq__(self, o: object) -> bool:
        # NOTE: This can be done better :)
        if not isinstance(o, AbstractVoteTarget):
            return NotImplemented
        if self.game != o.game:
            return False
        return repr(self) == repr(o)

    def __hash__(self) -> int:
        return hash(repr(self))


class VotingOptions(GameObject):
    """Voting options."""

    def __init__(
        self,
        game: Game,
        /,
        *,
        allow_unvote: bool = True,
        allow_against_all: bool = True,
    ):
        super().__init__(game)
        self._allow_unvote = bool(allow_unvote)
        self._allow_against_all = bool(allow_against_all)

    @property
    def allow_unvote(self) -> bool:
        return self._allow_unvote

    @property
    def allow_against_all(self) -> bool:
        return self._allow_against_all


class VotingResults(GameObject):
    """Voting results object."""

    def __init__(
        self,
        game: Game,
        /,
        *,
        allow_unvote: bool = True,
        allow_against_all: bool = True,
    ):
        super().__init__(game)
        self._voters: List[Actor] = []
        self._targets: List[GameObject] = []
        self._options = VotingOptions(
            allow_unvote=allow_unvote, allow_against_all=allow_against_all
        )

        def mk():
            return defaultdict(float)

        self._map: DefaultDict[int, DefaultDict[int, float]] = defaultdict(mk)

    @property
    def options(self) -> VotingOptions:
        return self._options

    @property
    def vote_counts(self) -> List[Tuple[GameObject, float]]:
        """Gets the vote counts, sorted in descending order."""
        res = []
        for i_t, t in enumerate(self._targets):
            total = 0
            for _, v in self._map.items():
                total += v[i_t]
            res.append((t, total))
        res = sorted(res, key=lambda x: -x[1])
        return res

    @property
    def vote_leaders(self) -> List[GameObject]:
        """Gets the current vote leaders, if any."""
        vc = self.vote_counts
        max_cnt = vc[0][1]
        res = []
        for target, cnt in vc:
            if cnt < max_cnt:
                break
            res.append(target)
        return res

    @inject_converters
    def _i_voter(self, voter: Actor) -> int:
        if voter in self._voters:
            i_voter = self._voters.index(voter)
        else:
            i_voter = len(self._voters)
            self._voters.append(voter)
        return i_voter

    @inject_converters
    def _i_target(self, target: GameObject) -> int:
        if target in self._targets:
            i_target = self._targets.index(target)
        else:
            i_target = len(self._targets)
            self._targets.append(target)
        return i_target

    def _reset(self, voter: Actor):
        i_src = self._i_voter(voter)
        self._map[i_src] = defaultdict(float)

    def _set_i(self, i_voter: int, i_target: int, weight: float = 1):
        self._map[i_voter][i_target] = weight

    def _get_i(self, i_voter: int, i_target: int) -> float:
        return self._map[i_voter][i_target]

    def _set(self, voter: Actor, target: GameObject, weight: float = 1):
        self._set_i(self._i_voter(voter), self._i_target(target), weight=weight)

    def _get(self, voter: Actor, target: GameObject) -> float:
        return self._get_i(self._i_voter(voter), self._i_target(target))


class UnvoteAll(AbstractVoteTarget):
    """Symbolic class for unvoting."""

    def apply(self, vr: VotingResults, source: Actor):
        """Removes all votes made by `source`."""
        if not vr.options.allow_unvote:
            # Warn?
            return
        vr._reset(source)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, UnvoteAll) and self.game == o.game:
            return True
        return False


class VoteAgainstAll(AbstractVoteTarget):
    """Symbolic class for voting against all options."""

    def apply(self, vr: VotingResults, source: Actor):
        """Unvotes-all, then votes for `VoteAgainstAll` object."""
        if not vr.options.allow_against_all:
            # Warn?
            return
        vr._reset(source)
        vr._set(
            source,
            VoteAgainstAll(self.game),
        )

    def __eq__(self, o: object) -> bool:
        if isinstance(o, VoteAgainstAll) and self.game == o.game:
            return True
        return False


class ActorTarget(AbstractVoteTarget):
    """Normal voting for a single Actor."""

    def __init__(self, game, /, actor: Actor):
        super().__init__(game)
        self._actor = actor

    @property
    def actor(self) -> Actor:
        return self._actor

    def apply(self, vr: VotingResults, source: Actor):
        vr._reset(source)
        vr._set(source, self.actor)


class ActorTargets(AbstractVoteTarget):
    """Voting for multiple actors."""

    def __init__(self, game, /, actors: List[Actor]):
        super().__init__(game)
        self._actors = list(actors)

    @property
    def actors(self) -> List[Actor]:
        return list(self._actors)

    def apply(self, vr: VotingResults, source: Actor):
        vr._reset(source)
        for a in self.actors:
            vr._set(source, a)


# TODO: Weighted votes?


class Vote(GameObject):
    """A vote on a Tally.

    Attributes
    ----------
    source : Actor
        The actor who is the source of the vote.
    target : AbstractVoteTarget
        The target, or targets, or UnvoteAll...

    TODO: tiebreaking, allow unvotes, allow against all?
    """

    def __init__(self, game: Game, /, source: Actor, target: AbstractVoteTarget):
        super().__init__(game)
        self.source = source
        self.target = target

    @property
    def source(self) -> Actor:
        return self._source

    @source.setter
    @inject_converters
    def source(self, v: Actor):
        if not isinstance(v, Actor):
            raise TypeError(f"Expected Actor, got {v!r}")
        self._source = v

    @property
    def target(self) -> AbstractVoteTarget:
        return self._target

    @target.setter
    @inject_converters
    def target(self, v: AbstractVoteTarget):
        if not isinstance(v, AbstractVoteTarget):
            raise TypeError(f"Expected AbstractVoteTarget, got {v!r}")
        self._target = v


class Tally(AuxObject):
    """Voting tally."""

    def __init__(self, game: Game, /):
        super().__init__(game)
        self._vote_history: List[Vote] = []

    @property
    def vote_history(self) -> List[Vote]:
        return list(self._vote_history)

    @property
    def results(self) -> VotingResults:
        """Applies vote history to get current results."""
        res = VotingResults(self.game)
        for v in self.vote_history:
            v.target.apply(res, v.source)
        return res


@converter.register
def get_vote_target_single(game: Game, obj: str) -> AbstractVoteTarget:
    """Parses a string as a vote target."""
    # TODO: Set phrases as game-specific options?
    if obj.lower() == "unvote":
        return UnvoteAll(game)
    elif obj.lower() == "no lynch":
        return VoteAgainstAll(game)
    return ActorTarget(game, actor=obj)  # will auto-convert the str, or fail.


@converter.register
def get_vote_target_multi(game: Game, obj: list) -> AbstractVoteTarget:
    """Parses a list of strings (or Actors) as a complex vote target."""
    # TODO: What if there are unvotes inside?...
    actors = [get_actor_by_name(game, x) for x in obj]
    return ActorTargets(game, actors=actors)


def get_vote_target(game: Game, obj: Union[str, list]) -> AbstractVoteTarget:
    if isinstance(obj, str):
        return get_vote_target_single(game, obj)
    elif isinstance(obj, list):
        return get_vote_target_multi(game, obj)
    raise TypeError(f"Can't get vote target for: {obj!r}")
