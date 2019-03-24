"""Module for Actors and Alignments.

:class:`Actor`'s are the entities that perform actions. 
This generally includes players and non-player characters. 

:class:`Alignment`'s are basically teams. The mechanism for determining 
game-ending and/or alignment-winning behavior is TBD.
"""

import logging
from mafia.core import GameObject
from mafia.core.event import Subscriber, ExternalEvent, EventManager
# from mafia.state.role import Role

from collections.abc import MutableMapping  


class BaseStatus(GameObject, MutableMapping):
    """Base status object.

    This behaves like a "Bunch" or "dotted dict". 
    Default keys are set, but you may add others. 
    Default values are None, unless given in `defaults`.

    Attributes
    ----------
    ID : UUID
        The UUID of this status, not of the Actor.

    Class Attributes
    ----------------
    defaults : dict
        Default values. If not given, they are None. 
    """

    defaults = {}

    def __init__(self, **kwargs):
        super().__init__() 
        for k, v in kwargs.items():
            setattr(self, k, v) 

    def __iter__(self):
        return iter(self.__dict__) 

    def __len__(self):
        return len(set(self.keys()))

    def __getattr__(self, k):
        try:
            super().__getattr__(k)
        except Exception:
            return self.defaults.get(k, None) 

    def __getitem__(self, k):
        return getattr(self, k, self.defaults.get(k, None))

    def __setitem__(self, k, value):
        setattr(self, k, value)

    def __delitem__(self, k):
        delattr(self, k) 


class Alignment(GameObject):
    """Defines an alignment (team).
    
    Attributes
    ----------
    name : str
        A human-readable name.
    members : list
        List of members of the alignment.
    """
    def __init__(self, name, members=[]):
        super().__init__()
        self.name = name
        self.members = list(members)

    def add(self, member):
        """Adds member to this alignment, removing old one."""
        if hasattr(member, 'alignment'):
            old_align = member.alignment
            if old_align is not None:
                old_align.remove(member)
        setattr(member, 'alignment', self)
        self.members.append(member)

    def remove(self, member):
        """Removes member from this alignment."""
        self.members.remove(member)
        if hasattr(member, 'alignment'):
            member.alignment = None


class ActorControlEvent(ExternalEvent):
    """Event for external control of an actor.
    
    Attributes
    ----------
    actor : Actor
        The actor being controlled.
    ability : Ability
        The ability to use.
    kwargs : dict
        Keyword arguments to give ability.
    """

    def __init__(self, actor, ability, **kwargs):
        super().__init__()
        self.actor = actor
        self.ability = ability
        self.kwargs = kwargs


class ActorStatus(BaseStatus):
    """Current actor status.

    This behaves like a "Bunch" or "dotted dict". 
    Default keys are set, but you may add others. 
    Default values are None, unless given in `defaults`.

    Attributes
    ----------
    alive : bool
        Whether this actor is alive.
    ID : UUID
        The UUID of this status, not of the Actor.

    Class Attributes
    ----------------
    defaults : dict
        Default values. If not given, they are None. 
    """

    defaults = {
        'alive': True
    }

    def __init__(self, alive=True, **kwargs):
        super().__init__(alive=alive, **kwargs) 


class Actor(GameObject, Subscriber):
    """A stateful object that performs actions.
    
    Attributes
    ----------
    name : str
        A human-readable name.
    alignment : Alignment
        Alignment (team) this actor is on.
    role : Role
        Role for this actor.
    status : ActorStatus
        Current status.
    """

    def __init__(self, name, alignment, role, status={}):
        super().__init__()
        self.name = name
        self.role = role
        self.status = ActorStatus(**status)
        # self.alignment = None
        alignment.add(self)

        EventManager.subscribe_me(
            self, ActorControlEvent,
            # TODO: other event types here
        )

    def __str__(self):
        return "[{}]".format(self.name)

    def respond_to_event(self, event):
        """Event handling mechanism."""
        if isinstance(event, ActorControlEvent) and event.actor is self:
            # TODO: Maybe check if self has that ability?..
            if event.ability not in self.role.abilities:
                logging.warning(
                    "Attempted to use ability that doesn't belong "
                    "to %s: %s" % (self, event.ability)
                )
                return None

            if not self.status['alive']:
                logging.warning(
                    "Attempted to use ability for dead actor: %s" % self
                )

            # Use the activated ability
            return event.ability.activate(self, **event.kwargs)
