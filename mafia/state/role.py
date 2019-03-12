"""Base classes for abilities and roles.

An :class:`Ability` specifies the potential for an :class:`Actor` to 
perform an :class:`Action`. 

An :class:`ActivatedAbility` is activated by the actor directly, while 
a :class:`TriggeredAbility` is triggered by some external event. You can 
think of these as "active" and "passive/reactive" abilities respectively.
"""

from copy import deepcopy
from mafia.core import GameObject
# from mafia.core.event import EventManager  # , ExternalEvent, Subscriber, 


class Ability(GameObject):
    """Base class for all abilities."""

    def __init__(self):
        super().__init__()


class ActivatedAbility(Ability):
    """Activated ability base class."""

    def __init__(self):
        super().__init__()

    def activate(self, actor, **kwargs):
        # TODO: Set some sort of internal event
        print('activated')
        pass


class TriggeredAbility(Ability):
    """Triggered (passive) ability base class."""

    def __init__(self):
        super().__init__()

    def trigger(self):
        # TODO: Set some sort of internal event
        print('triggered')
        pass


class Role(GameObject):
    """A role is a set of abilities."""

    def __init__(self, abilities=[]):
        super().__init__()
        self.abilities = [deepcopy(a) for a in abilities]
