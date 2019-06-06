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

from mafia.mechanics.vote import LynchTally, VoteAbility, ResolveVotesAbility
from mafia.mechanics.kill import KillAbility
from mafia.mechanics.restriction import PhaseUse


lynch_tally = LynchTally("lynch-tally")
phase_state = PhaseState()
game = Game(status={"tally": lynch_tally, "phase": phase_state})


def day():
    return PhaseUse(phase_state=phase_state, allowed_phases=[0])


def night():
    return PhaseUse(phase_state=phase_state, allowed_phases=[1])


with game:
    mafia = Alignment("mafia")
    town = Alignment("town")

    mod = Moderator(
        "Mod",
        abilities=[
            PhaseChangeAbility("change-phase", phase_state=phase_state),
            ResolveVotesAbility("resolve-votes", tally=lynch_tally),
        ],
    )

    alice = Actor(
        "Alice",
        alignments=[mafia],
        abilities=[
            VoteAbility("alice-vote", tally=lynch_tally, restrictions=[day()]),
            KillAbility("mafia-kill", restrictions=[night()]),
        ],
        status={"baddie": True},
    )
    bob = Actor(
        "Bob",
        alignments=[town],
        abilities=[VoteAbility("bob-vote", tally=lynch_tally, restrictions=[day()])],
    )
    charlie = Actor(
        "Charles",
        alignments=[town],
        abilities=[
            VoteAbility("charles-vote", tally=lynch_tally, restrictions=[day()])
        ],
    )

    def vote(src, trg):
        va = [a for a in src.abilities if isinstance(a, VoteAbility)]
        taa = TryActivateAbility(va[0], target=trg)
        game.handle_event(taa)

    def mafiakill(src, trg):
        mk = [a for a in src.abilities if isinstance(a, KillAbility)]
        t = TryActivateAbility(mk[0], target=trg)
        game.handle_event(t)

    def change_phase(new_phase=None):
        pca = [a for a in mod.abilities if isinstance(a, PhaseChangeAbility)]
        rva = [a for a in mod.abilities if isinstance(a, ResolveVotesAbility)]
        t1 = TryActivateAbility(rva[0])
        t2 = TryActivateAbility(pca[0], new_phase=new_phase)
        game.handle_event(t1)
        game.handle_event(t2)


# Start of game
print(phase_state)

# Day 1 votes
vote(alice, bob)
# vote(alice, charlie)
print("Vote leaders:", [a.name for a in lynch_tally.vote_leaders])
change_phase()

print("Bob is alive:", bob.status.alive.value)
print(phase_state)

# Night 1 stuff
mafiakill(alice, charlie)
change_phase()
print("Charlie is alive:", charlie.status.alive.value)
print(phase_state)
# print(game.status.phase.value)

