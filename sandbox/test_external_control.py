from mafia.core.event import EventManager
from mafia.state.role import Role, ActivatedAbility, TriggeredAbility
from mafia.state.actor import Actor, ActorControlEvent, Alignment

ta = TriggeredAbility('ta')
aa = ActivatedAbility('aa')

role = Role([ta, aa])
alignment = Alignment('good boys')
actor = Actor('Tolik', alignment, role, {})

print(len(EventManager.members))

ace = ActorControlEvent(actor, aa)

EventManager.handle_event(ace)
