import logging

from mafia.premade.template.vanilla import VanillaGame, VoteAbility
from mafia.core.event import EventManager
# from mafia.state.role import Role, ActivatedAbility, TriggeredAbility
from mafia.state.actor import ActorControlEvent  # , Actor, Alignment

logging.basicConfig(level=logging.DEBUG)

# Generate game
vg = VanillaGame.generate(5)


# Helper functions


def vote(src, trg):
    abil = [
        a for a in src.role.abilities 
        if isinstance(a, VoteAbility)
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
    print(", ".join([
        str(k) for k in vg.actors 
        if k.status['alive']])
    )


# Day 1
print_alive()

vote(vg.actors[1], vg.actors[2])
vote(vg.actors[0], vg.actors[1])
vote(vg.actors[1], vg.actors[0])
vote(vg.actors[2], vg.actors[1])
vote(vg.actors[3], vg.actors[1])

print_votes()

next(vg.phase_state)

# Night 1
print_alive()

# NOTE: Shouldn't be allowed to vote here :D
vote(vg.actors[0], vg.actors[2]) 
print_votes()

next(vg.phase_state)

# Day 2
print_alive()

# Allowed to vote now
vote(vg.actors[0], vg.actors[2]) 
print_votes()

next(vg.phase_state)

# Night 2
print_alive()
