
# from mafia.core.event import InternalEvent, Subscriber, EventManager
from mafia.core.action import Action  # , PreActionEvent, PostActionEvent
from mafia.state.role import ActivatedAbility


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
        pass  # TODO: Need to cause death 


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
        print("{} is killing {}".format(
            actor.name, getattr(target, 'name'))
        )
        # TODO: Add "do the thing" here. 
