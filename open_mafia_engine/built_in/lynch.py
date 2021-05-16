from typing import Optional, Union, Type

from open_mafia_engine.core import (
    Ability,
    ActivatedAbility,
    Action,
    Actor,
    EPostPhaseChange,
    EPrePhaseChange,
    Event,
    Game,
)

from .killing import KillAction
from .voting import (
    SimpleVoteAction,
    SimpleVoteTally,
    UnvoteAll,
    VoteAgainstAll,
    VoteForActor,
    VoteForActors,
)


class LynchAction(KillAction):
    """This lynches the target, who is decided based on the tally."""

    def doit(self, game: Game) -> None:
        # victim = [x for x in game.actors if x == self.target][0]
        victim = self.target
        if victim is None:
            # FIXME: Remove
            print(f"Nobody was lynched [should never have made action - bug?]")
        else:
            victim: Actor
            victim.status["dead"] = True  # or 'alive' = False
            print(f"The town has lynched {victim.name}")  # FIXME: Remove


_SimpleLynchVote = Union[UnvoteAll, VoteAgainstAll, VoteForActors, VoteForActor]


class SimpleLynchTally(SimpleVoteTally):
    """Basic voting for Mafia, including a multi-voting option."""

    def _chk_vote(self, vote: _SimpleLynchVote):
        super()._chk_vote(vote)
        if not isinstance(vote, (UnvoteAll, VoteAgainstAll, VoteForActors)):
            raise TypeError(f"Unexpected vote type: {vote!r}")

    def select_leader(self) -> Optional[Actor]:
        return super().select_leader()

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
                    print("Nobody was lynched.")  # FIXME: Remove
                    return None
                return LynchAction(source=self, target=leader)
        elif isinstance(event, EPostPhaseChange):
            if event.new_phase.name == "day":
                self.clear()


class SimpleLynchVoteAction(SimpleVoteAction):
    """Casts a single vote on a tally."""

    def __init__(
        self,
        source: Ability,
        tally: Optional[SimpleVoteTally] = None,
        target: Union[None, Actor, Type[UnvoteAll], Type[VoteAgainstAll]] = None,
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
        # Figure out which tally to use
        if self.tally is None:
            tallies = game.aux.filter_by_type(SimpleLynchTally)
            if len(tallies) != 1:
                raise ValueError(f"Could not determine proper tally: {tallies}")
            tally: SimpleVoteTally = tallies[0]
        else:
            tally = self.tally
        # Figure out what type of vote to add
        if (self.target is UnvoteAll) or (self.target is None):
            print(f"{source.name} unvoted.")  # FIXME: Remove
            tally.add(UnvoteAll(source=source))
        elif self.target is VoteAgainstAll:
            print(f"{source.name} voted for No-Lynch.")
            tally.add(VoteAgainstAll(source=source))
        else:
            print(f"{source.name} voted for {self.target.name}!")  # FIXME: Remove
            tally.add(VoteForActor(source=source, targets=[self.target]))


SimpleLynchVoteAbility = ActivatedAbility.create_type(
    SimpleLynchVoteAction, "SimpleLynchVoteAbility"
)
