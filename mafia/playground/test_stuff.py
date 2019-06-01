"""Informal test of various systems

"""

# flake8: noqa

from mafia.core.event import EventManager, Subscriber, Action
from mafia.core.ability import (
    ActivatedAbility,
    TriggeredAbility,
    TryActivateAbility,
    IllegalAbilityActivation,
)
from mafia.state.actor import Alignment, Actor, Moderator
from mafia.state.game import Game, PhaseState, PhaseChangeAbility


class VoteAction(Action):
    """Fake vote action."""

    def __init__(self, source: Actor, target: Actor):
        self.source = source
        self.target = target

    def __execute__(self) -> bool:
        print("%s voted for %s" % (self.source.name, self.target.name))
        return True


class VoteAbility(ActivatedAbility):
    """Fake vote ability."""

    def is_legal(self, target: Actor):
        if not isinstance(target, Actor):
            return False
        return True

    def activate(self, target: Actor) -> VoteAction:
        super().activate(target=target)
        return VoteAction(self.owner, target)


game = Game()

with game:
    mafia = Alignment("mafia")
    town = Alignment("town")

    mod = Moderator(
        "Mod",
        abilities=[
            PhaseChangeAbility("change-phase", phase_state=game.status.phase.value)
        ],
    )

    alice = Actor(
        "Alice",
        alignments=[mafia],
        abilities=[VoteAbility("alice-vote")],
        status={"baddie": True},
    )
    bob = Actor("Bob", alignments=[town], abilities=[VoteAbility("bob-vote")])
    charlie = Actor("Charles", alignments=[town], abilities=[VoteAbility("c-vote")])

    def vote(src, trg):
        va = [a for a in src.abilities if isinstance(a, VoteAbility)]
        taa = TryActivateAbility(va[0], target=trg)
        game.handle_event(taa)

    def change_phase(new_phase=None):
        pca = [a for a in mod.abilities if isinstance(a, PhaseChangeAbility)]
        taa = TryActivateAbility(pca[0], new_phase=new_phase)
        game.handle_event(taa)


# Start of game
print(game.status.phase.value)

# Day 1 votes
vote(alice, bob)
change_phase()
print(game.status.phase.value)

# Night 1 stuff
# TODO
change_phase()
print(game.status.phase.value)
