from collections import Counter
import random

from open_mafia_engine.core import *


class Vote(GameObject):
    """Simple single vote. Votes with `target=None` are no-lynch votes. No unvotes.

    TODO: Actually make multi-target votes a thing.
    TODO: Make AbstractVote, then this will be VoteActor? Or generics?
    """

    def __init__(self, source: Actor, target: Optional[Actor] = None):
        self.source = source
        self.target = target

    @property
    def source(self) -> Actor:
        return self._source

    @source.setter
    def source(self, value: Actor):
        if not isinstance(value, Actor):
            raise TypeError(f"Source is not an Actor: {value!r}")
        self._source = value

    @property
    def target(self) -> Optional[Actor]:
        return self._target

    @target.setter
    def target(self, value: Optional[Actor]):
        if value is None:
            pass
        elif not isinstance(value, Actor):
            raise TypeError(f"Target is not an Actor: {value!r}")
        self._target = value


class VoteTally(AuxGameObject):
    """Keeps votes; very simplistic, handling unvotes."""

    def __init__(self, votes: List[Vote] = None, *, select_on_tie: bool = False):
        if votes is None:
            votes = []
        self._votes = list(votes)
        self._select_on_tie = bool(select_on_tie)

    @property
    def select_on_tie(self) -> bool:
        return self._select_on_tie

    @property
    def votes(self) -> List[Vote]:
        return list(self._votes)

    def add(self, vote: Vote):
        """Adds the vote to this tally. To unvote, use a vote with target=None."""
        for old_v in self._votes:
            if old_v.source == vote.source:
                self._votes.remove(old_v)
                break
        self._votes.append(vote)

    @property
    def leaders(self) -> List[Optional[Actor]]:
        """The actors with the most votes."""
        if len(self._votes) == 0:
            return []
        cnt = Counter([x.target for x in self._votes])
        top_votes = cnt.most_common(1)[0][1]
        res = [a for (a, c) in cnt.most_common() if c == top_votes]
        return res

    def select_leader(self) -> Optional[Actor]:
        """Selects a single vote leader.

        This may be random, if tied and `select_on_tie`.
        """
        leaders = self.leaders
        if len(leaders) == 0:
            return None
        elif len(leaders) == 1:
            return leaders[0]
        # len > 1
        if self.select_on_tie:
            logging.info(f"Selecting from leaders: {leaders}")
            return random.choice(leaders)
        return None


class VoteAction(Action):
    """Fake vote for the target."""

    def __init__(
        self,
        source: Ability,
        target: Actor = None,
        *,
        priority: float = 1.0,
        canceled: bool = False,
    ):
        super().__init__(source, priority=priority, canceled=canceled)
        self.target = target

    def doit(self, game: Game) -> None:
        abil: Ability = self.source
        source: Actor = abil.owner
        print(f"{source.name} voted for {self.target.name}!")
        tallies = game.aux.filter_by_type(VoteTally)
        if len(tallies) != 1:
            raise ValueError(f"Could not determine proper tally: {tallies}")
        tally: VoteTally = tallies[0]
        tally.add(Vote(source=source, target=self.target))


VoteAbility = ActivatedAbility.create_type(VoteAction, name="VoteAbility")
# VoteAbility = ActivatedAbility[VoteAction]  # alternate, but badly named


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
            print(f"Nobody was killed by {src.owner.name}")
        else:
            victim: Actor
            victim.status["dead"] = True  # or 'alive' = False
            print(f"{src.owner.name} killed {victim.name}")


KillAbility = ActivatedAbility[KillAction]


class LynchAction(KillAction):
    """This lynches the target, who is decided based on the tally."""

    def doit(self, game: Game) -> None:
        # victim = [x for x in game.actors if x == self.target][0]
        victim = self.target
        if victim is None:
            print(f"Nobody was lynched [should never have made action - bug?]")
        else:
            victim: Actor
            victim.status["dead"] = True  # or 'alive' = False
            print(f"The town has lynched {victim.name}")


class LynchTally(VoteTally):
    """A hacking vote tally that lynches folks during the day, and resets."""

    def __subscribe__(self, game: Game) -> None:
        game.add_sub(self, EPrePhaseChange, EPostPhaseChange)

    def __unsubscribe__(self, game: Game) -> None:
        game.remove_sub(self, EPrePhaseChange, EPostPhaseChange)

    def respond_to_event(self, event: Event, game: Game) -> Optional[Action]:
        # TODO: Maybe instead of clearing, we re-create the lynch tally? ...
        if isinstance(event, EPrePhaseChange):
            if event.old_phase.name == "day":
                leader = self.select_leader()
                if leader is None:
                    print("Nobody was lynched.")
                    return None
                return LynchAction(source=self, target=leader)
        elif isinstance(event, EPostPhaseChange):
            if event.new_phase.name == "day":
                self._votes = []


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
