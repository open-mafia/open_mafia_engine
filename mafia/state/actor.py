
from mafia.core import GameObject
from mafia.core.event import Subscriber, ExternalEvent, EventManager
# from mafia.state.role import Role


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
        self.members = members

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
    status : dict
        Current status.
    """

    def __init__(self, name, alignment, role, status):
        super().__init__()
        self.name = name
        self.role = role
        self.status = status
        # self.alignment = None
        alignment.add(self)

        EventManager.subscribe_me(
            self, ActorControlEvent,
            # TODO: other event types here
        )

    def __str__(self):
        return "{name}".format(self.__dict__)

    def respond_to_event(self, event):
        """Event handling mechanism."""
        if isinstance(event, ActorControlEvent) and event.actor is self:
            # TODO: Maybe check if self has that ability?..

            # Use the activated ability
            event.ability.activate(self, **event.kwargs)
