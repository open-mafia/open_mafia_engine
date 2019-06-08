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
from mafia.mechanics.restriction import (
    PhaseUse,
    NUse,
    UseTracker,
    UseTrackerPerPhase,
    MustBeAlive,
)


lynch_tally = LynchTally("lynch-tally")
phase_state = PhaseState()
game = Game(status={"tally": lynch_tally, "phase": phase_state})


def day():
    return PhaseUse(phase_state=phase_state, allowed_phases=["day"])


def night():
    return PhaseUse(phase_state=phase_state, allowed_phases=["night"])


def a_vote():
    return VoteAbility("vote", tally=lynch_tally, restrictions=[MustBeAlive(), day()])


mafia_kill_tracker = UseTrackerPerPhase(1)


def a_mkill():
    return KillAbility(
        "mafia-kill",
        restrictions=[MustBeAlive(), night(), NUse(tracker=mafia_kill_tracker)],
    )


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

    # 2 mafia, 3 town
    players = []
    for _name in ["Alice", "Bob"]:
        _p = Actor(
            _name,
            alignments=[mafia],
            abilities=[a_vote(), a_mkill()],
            status={"baddie": True},
        )
        players.append(_p)

    for _name in ["Charles", "Dave", "Emily"]:
        _p = Actor(_name, alignments=[town], abilities=[a_vote()])
        players.append(_p)

    a, b, c, d, e = players

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

    def print_status():
        print("----------------")
        print("Phase:", phase_state)
        if phase_state.current == "day":
            print("Vote leaders:", [a.name for a in lynch_tally.vote_leaders])
        print("Alive players: ", [a.name for a in game.actors if a.status.alive.value])


# Start of game
print_status()

# Day 1 votes
vote(a, b)
vote(b, c)
vote(d, c)
print_status()

change_phase()
print_status()

# Night 1 mafia kill
mafiakill(a, e)
mafiakill(b, d)  # this will fail, correctly

change_phase()
print_status()

# Day 2 votes
vote(a, d)
vote(b, a)
vote(b, d)
