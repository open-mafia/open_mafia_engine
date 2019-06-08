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
from mafia.mechanics.outcome import WhenEliminated, WhenHasOutcome

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


lynch_tally = LynchTally("lynch-tally")
phase_state = PhaseState()
game = Game(status={"tally": lynch_tally, "phase": phase_state})

with game:
    # Create aux objects
    mafia_kill_tracker = UseTrackerPerPhase(1)

    def day():
        return PhaseUse(phase_state=phase_state, allowed_phases=["day"])

    def night():
        return PhaseUse(phase_state=phase_state, allowed_phases=["night"])

    def a_vote():
        return VoteAbility(
            "vote", tally=lynch_tally, restrictions=[MustBeAlive(), day()]
        )

    def a_mkill():
        return KillAbility(
            "mafia-kill",
            restrictions=[MustBeAlive(), night(), NUse(tracker=mafia_kill_tracker)],
        )

    # Create alignments
    mafia = Alignment("mafia")
    town = Alignment("town")
    mafia_ally = Alignment("mafia-ally")
    jester = Alignment("jester")

    # Add outcome checkers
    oc_mafia_win = WhenEliminated(mafia, watched=town, victory=True)
    oc_mafia_lose = WhenEliminated(mafia, watched=mafia, victory=False)
    # oc_town_win = WhenEliminated(town, watched=[mafia, mafia_ally], victory=True)
    # oc_town_lose = WhenEliminated(town, watched=town, victory=False)
    oc_town = WhenHasOutcome(town, watched=mafia, when_victory=False, when_defeat=True)
    oc_mally = WhenHasOutcome(
        mafia_ally, watched=mafia, when_victory=True, when_defeat=False
    )
    # NOTE: Temp, not actually jester
    oc_jester = WhenEliminated(jester, watched=jester, victory=True)

    # Add players
    # (moderator can be a player too, btw, but here he's without alignment)
    mod = Moderator(
        "Mod",
        abilities=[
            PhaseChangeAbility("change-phase", phase_state=phase_state),
            ResolveVotesAbility("resolve-votes", tally=lynch_tally),
        ],
    )

    # 2 mafia
    players = []
    for _name in ["Alice", "Bob"]:
        _p = Actor(
            _name,
            alignments=[mafia],
            abilities=[a_vote(), a_mkill()],
            status={"baddie": True},
        )
        players.append(_p)

    # 3 vanilla town
    for _name in ["Charles", "Dave", "Emily"]:
        _p = Actor(_name, alignments=[town], abilities=[a_vote()])
        players.append(_p)

    # 1 mafia-ally
    players.append(Actor("Fred", alignments=[mafia_ally], abilities=[a_vote()]))

    # 1 jester
    players.append(Actor("Gwen", alignments=[jester], abilities=[a_vote()]))

    #

    a, b, c, d, e, f, g = players

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
        print("----------------")


# Day 1
print_status()
# lynch a townie
vote(a, b)
vote(b, c)
vote(d, c)

change_phase()

# Night 1
print_status()
# mafia kill
mafiakill(a, e)
mafiakill(b, d)  # this will fail, correctly

change_phase()

# Day 2 votes
print_status()
# lynch the jester
vote(a, g)
vote(d, g)
vote(b, d)
vote(g, g)

change_phase()

# Night 2
print_status()
# mafia kill the final townie
mafiakill(b, d)
# print_status()
