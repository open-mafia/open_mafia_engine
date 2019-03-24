import logging

from mafia.premade.template.vanilla import (
    VanillaGame, VoteAbility, KillAbility
)
from mafia.core.event import EventManager
# from mafia.state.role import Role, ActivatedAbility, TriggeredAbility
from mafia.state.actor import ActorControlEvent  # , Actor, Alignment

import random

logging.basicConfig(level=logging.DEBUG)

# Generate game
vg = VanillaGame.generate(5)


# Helper functions


def list_alive(team=None):
    if team is None:
        pool = vg.actors
    else:
        pool = [
            al for al in vg.alignments
            if al.name == team
        ][0].members

    act_alive = [
        ac for ac in pool
        if ac.status['alive']
    ]
    return act_alive


def vote(src, trg):
    abil = [
        a for a in src.role.abilities 
        if isinstance(a, VoteAbility)
    ][0]
    ace = ActorControlEvent(src, abil, target=trg)
    EventManager.handle_event(ace)


def random_vote():
    src, trg = random.choices(list_alive(), k=2)
    vote(src, trg)


def random_mkill():
    # Not-actually-random Mafia night kill
    
    src = random.choice(list_alive(team='mafia'))
    trg = random.choice(list_alive(team='town'))

    abil = [
        a for a in src.role.abilities 
        if isinstance(a, KillAbility)
    ][0]
    ace = ActorControlEvent(src, abil, target=trg)
    EventManager.handle_event(ace)


def print_votes():
    print(
        " | ".join([
            "%s->%s" % (k.name, v.name) for k, v 
            in vg.vote_tally.votes_for.items()
        ])
    )


def print_alive():
    print(", ".join([str(k) for k in list_alive()]))

    if len(list_alive(team='town')) == 0:
        print("Mafia have won!")

    if len(list_alive(team='mafia')) == 0:
        print("Town have won!")


# Day 1

print_alive()

"""
vote(vg.actors[1], vg.actors[2])
vote(vg.actors[0], vg.actors[1])
vote(vg.actors[1], vg.actors[0])
vote(vg.actors[2], vg.actors[1])
vote(vg.actors[3], vg.actors[1])
"""

for i in range(5):
    random_vote()

print_votes()

next(vg.phase_state)

# Night 1
print_alive()

# NOTE: Shouldn't be allowed to vote here :D
random_vote()
print_votes()

# Instead we just kill a dude at random
random_mkill()

next(vg.phase_state)

# Day 2
print_alive()

# Allowed to vote now
random_vote()
print_votes()

next(vg.phase_state)

# Night 2
print_alive()

random_mkill()

next(vg.phase_state)

# Day 3
print_alive()
