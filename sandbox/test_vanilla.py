import logging

from mafia.premade.template.vanilla import VanillaGame
from mafia.core.event import EventManager
# from mafia.state.role import Role, ActivatedAbility, TriggeredAbility
from mafia.state.actor import ActorControlEvent  # , Actor, Alignment

logging.basicConfig(level=logging.DEBUG)


vg = VanillaGame.generate(5)
m1 = vg.actors[0]
t1 = vg.actors[2]
m1v = m1.role.abilities[0]
t1v = t1.role.abilities[0]

vg.phase_state

ace = ActorControlEvent(m1, m1v, target=t1)
EventManager.handle_event(ace)

vg.vote_tally
