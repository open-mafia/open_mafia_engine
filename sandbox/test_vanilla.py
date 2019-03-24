import logging

from mafia.premade.template.vanilla import VanillaGame, VoteAbility
from mafia.core.event import EventManager
# from mafia.state.role import Role, ActivatedAbility, TriggeredAbility
from mafia.state.actor import ActorControlEvent  # , Actor, Alignment

logging.basicConfig(level=logging.DEBUG)


vg = VanillaGame.generate(5)
vg.phase_state


def vote(src, trg):
    abil = [
        a for a in src.role.abilities 
        if isinstance(a, VoteAbility)
    ][0]
    ace = ActorControlEvent(src, abil, target=trg)
    EventManager.handle_event(ace)


vote(vg.actors[1], vg.actors[2])
vote(vg.actors[0], vg.actors[1])
vote(vg.actors[1], vg.actors[0])
vote(vg.actors[2], vg.actors[1])
vote(vg.actors[3], vg.actors[1])


print(
    " | ".join([
        "%s->%s" % (k.name, v.name) for k, v 
        in vg.vote_tally.votes_for.items()
    ])
)

next(vg.phase_state)
