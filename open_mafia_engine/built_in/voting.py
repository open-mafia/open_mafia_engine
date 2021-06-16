from __future__ import annotations

import logging
from abc import abstractmethod
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional, Tuple, Union

from open_mafia_engine.core.all import (
    Ability,
    Action,
    Actor,
    AuxObject,
    EPostAction,
    EPostPhaseChange,
    EPreAction,
    Game,
    GameObject,
    PhaseChangeAction,
    converter,
    get_actor_by_name,
    handler,
    inject_converters,
)

NoneType = type(None)
logger = logging.getLogger(__name__)

# TODO: tiebreaking enum, hammers, allow unvotes, allow against all


class AbstractVoteTarget(GameObject):
    """A target for voting. Don't use directly."""

    @abstractmethod
    def apply(self, vr: VotingResults, voter: Actor):
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
    """Voting options.

    Attributes
    ----------
    game : Game
    allow_unvote : bool
        Whether unvotes are allowed at all. Default is True.
    allow_against_all : bool
        Whether a "VoteAgainstAll" (e.g. "no lynch") is allowed. Default is True.

    TODO: Hammers? Tiebreaks?
    """

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
        options: VotingOptions,
        /,
    ):
        super().__init__(game)
        self._voters: List[Actor] = []
        self._targets: List[GameObject] = []
        self._options = options

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
        if len(vc) == 0:
            return []

        max_cnt = vc[0][1]
        # This short-circuits any votes :)
        if max_cnt <= 0:
            return []

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

    def apply(self, vr: VotingResults, voter: Actor):
        """Removes all votes made by `voter`."""
        if not vr.options.allow_unvote:
            # Warn?
            return
        vr._reset(voter)

    def __eq__(self, o: object) -> bool:
        if isinstance(o, UnvoteAll) and self.game == o.game:
            return True
        return False


class VoteAgainstAll(AbstractVoteTarget):
    """Symbolic class for voting against all options."""

    def apply(self, vr: VotingResults, voter: Actor):
        """Unvotes-all, then votes for `VoteAgainstAll` object."""
        if not vr.options.allow_against_all:
            # Warn?
            return
        vr._reset(voter)
        vr._set(
            voter,
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

    def apply(self, vr: VotingResults, voter: Actor):
        vr._reset(voter)
        vr._set(voter, self.actor)


class ActorTargets(AbstractVoteTarget):
    """Voting for multiple actors."""

    def __init__(self, game, /, actors: List[Actor]):
        super().__init__(game)
        self._actors = list(actors)

    @property
    def actors(self) -> List[Actor]:
        return list(self._actors)

    def apply(self, vr: VotingResults, voter: Actor):
        vr._reset(voter)
        for a in self.actors:
            vr._set(voter, a)


# TODO: Weighted votes? Weighted targets?


class Vote(GameObject):
    """A vote on a Tally.

    Attributes
    ----------
    voter : Actor
        The actor who is voting.
    target : AbstractVoteTarget
        The target, or targets, or UnvoteAll...
    """

    def __init__(self, game: Game, /, voter: Actor, target: AbstractVoteTarget):
        super().__init__(game)
        self.voter = voter
        self.target = target

    @property
    def voter(self) -> Actor:
        return self._source

    @voter.setter
    @inject_converters
    def voter(self, v: Actor):
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


class VoteAction(Action):
    """Votes for someone."""

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        voter: Actor,
        target: AbstractVoteTarget,
        tally: Tally = None,
        *,
        priority: float = 0.0,
        canceled: bool = False,
    ):
        super().__init__(game, source, priority=priority, canceled=canceled)
        self.voter = voter
        self.target = target
        if tally is None:
            tally = get_default_tally(game, tally)
        self.tally = tally

    def doit(self):
        self.tally.add_vote(Vote(self.game, voter=self.voter, target=self.target))

    class Pre(EPreAction):
        """We are about to vote."""

    class Post(EPostAction):
        """We have voted."""


class Tally(AuxObject):
    """Voting tally.

    Tallies select the leader before each phase end. Override `respond_leader()`.
    Tallies reset after each phase end.
    """

    def __init__(
        self,
        game: Game,
        /,
        *,
        allow_unvote: bool = True,
        allow_against_all: bool = True,
    ):
        super().__init__(game)
        self._vote_history: List[Vote] = []
        self._options = VotingOptions(
            game, allow_unvote=allow_unvote, allow_against_all=allow_against_all
        )

    @abstractmethod
    def respond_leader(self, leader: GameObject) -> Optional[List[Action]]:
        """Override this for particular behavior."""
        return None

    @property
    def options(self) -> VotingOptions:
        return self._options

    @property
    def allow_unvote(self) -> bool:
        return self.options.allow_unvote

    @property
    def allow_against_all(self) -> bool:
        return self.options.allow_against_all

    @property
    def vote_history(self) -> List[Vote]:
        return list(self._vote_history)

    @property
    def results(self) -> VotingResults:
        """Applies vote history to get current results."""
        res = VotingResults(self.game, self.options)
        for v in self.vote_history:
            v.target.apply(res, v.voter)
        return res

    def add_vote(self, vote: Vote):
        """Adds the vote to history."""
        if not isinstance(vote, Vote):
            raise TypeError(f"Can only add a Vote, got {vote!r}")
        self._vote_history.append(vote)

    @handler
    def reset_on_phase(self, event: EPostPhaseChange):
        """Resets votes every phase change."""
        self._vote_history = []

    @handler
    def handle_leader(self, event: PhaseChangeAction.Pre):
        leaders = self.results.vote_leaders
        if len(leaders) == 0:
            return
        elif len(leaders) > 1:
            return  # TODO: Tiebreaks, but they must be deterministic!
        leader = leaders[0]
        return self.respond_leader(leader)

    @handler
    def check_hammer(self, event: VoteAction.Post):
        """TODO: Hammers."""

        # Check if hammers are set.
        # If yes, check if this vote hammers.
        # If yes, end the phase.


class VoteAbility(Ability):
    """Voting ability."""

    def __init__(
        self,
        game: Game,
        /,
        owner: Actor,
        name: str,
        tally: Tally = None,
        desc: str = "Voting ability.",
    ):
        super().__init__(game, owner, name, desc=desc)
        self.tally = tally  # Is this found by the Injector?...

    def activate(self, target: AbstractVoteTarget) -> Optional[List[VoteAction]]:
        """Creates the action."""

        # TODO: Constraints!

        try:
            return [
                VoteAction(
                    self.game, self, voter=self.owner, target=target, tally=self.tally
                )
            ]
        except Exception:
            logger.exception("Error executing action:")
            if False:  # True, if debugging?
                raise
            return None


@converter.register
def get_default_tally(game: Game, obj: NoneType) -> Tally:
    """Selects the default vote tally."""
    tallies: List[Tally] = game.aux.filter_by_type(Tally)
    if len(tallies) == 0:
        raise TypeError(f"No tallies found!")
    elif len(tallies) > 1:
        raise TypeError(f"Multiple tallies found: {tallies!r}")
    return tallies[0]


@converter.register
def get_vote_target_actor(game: Game, obj: Actor) -> AbstractVoteTarget:
    return ActorTarget(game, actor=obj)


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
