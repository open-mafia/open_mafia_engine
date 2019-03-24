
# from mafia.core.event import InternalEvent, Subscriber, EventManager
from mafia.core.action import Action  # , PreActionEvent, PostActionEvent
from mafia.state.role import ActivatedAbility

import logging


class KillAction(Action):
    """Action that causes death.
    
    Attributes
    ----------
    source : GameObject
        Who/what is killing; usually an :class:`Actor`.
    target : GameObject
        Who/what is being killed; usually an :class:`Actor`). 
    """

    def __init__(self, source, target):
        self.source = source
        self.target = target

    def _execute(self):
        logging.debug("{} is killing {}".format(
            getattr(self.source, 'name'), 
            getattr(self.target, 'name'),
        ))
        t = self.target
        if hasattr(t, 'status'):
            t.status['alive'] = False
        # TODO: Need to cause death correctly - maybe rethink? 


class KillAbility(ActivatedAbility):
    """Allows an actor to kill.
    
    Attributes
    ----------
    name : str
        Ability name (human-readable).
    """

    def __init__(self, name):
        super().__init__(name=name)

    def activate(self, actor, target=None):
        if target is None:
            return None
        return KillAction(actor, target=target)
