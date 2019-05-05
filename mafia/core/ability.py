"""Base classes for abilities.

An :class:`Ability` specifies the potential for an :class:`Actor` (or 
another object, such as a :class:`Game`) to perform an :class:`Action`. 

An :class:`ActivatedAbility` is activated by the actor directly, while 
a :class:`TriggeredAbility` is triggered by some external event. You can 
think of these as "active" and "passive/reactive" abilities respectively.
"""

from typing import Optional
from mafia.util import ReprMixin
from mafia.core.errors import MafiaError
from mafia.core.event import Action, Subscriber, Event


class Ability(ReprMixin):
    """Base class for all abilities.

    The `owner` is the object the ability belongs to. 
    It is usually, but not necessarily, an :class:`Actor`.
    
    Attributes
    ----------
    owner : object
        The object that owns the ability.
    name : str
        Ability name (human-readable).
    """

    def __init__(self, owner, name: str):
        super().__init__()
        self.owner = owner
        self.name = name


class TryActivateAbility(Event):
    """Event for signalling intent to activate an ability.
    
    Attributes
    ----------
    ability : Ability
        The ability to use.
    kwargs : dict
        Keyword arguments to give ability.
    """

    def __init__(self, ability, **kwargs):
        super().__init__()
        self.ability = ability
        self.kwargs = kwargs


class ActivatedAbility(Ability, Subscriber):
    """Activated ability base class.

    To implement an activated ability, override 
    :meth:`activate`, with proper arguments, to return 
    the :class:`Action` (or `None`) to perform.

    Note that activate won't be called directly from the 
    code, but will instead be caused by an event. 
    
    Attributes
    ----------
    owner : object
        The object that owns the ability.
    name : str
        Ability name (human-readable).
    """

    def __init__(self, owner, name: str):
        super().__init__(owner, name)
        self.subscribe_to(TryActivateAbility)

    def is_legal(self, **kwargs) -> bool:
        """Check whether the ability usage is legal. Override this.

        This is used to pre-filter possible targets and improve 
        user experience (i.e. preventing impossible actions).
        Ideally, this is a lightweight operation.
        
        Parameters
        ----------
        kwargs : dict
            Keyword arguments of the ability usage.

        Returns
        -------
        can_use : bool
            Whether the ability usage is legal.
        """
        return True

    def activate(self, **kwargs) -> Optional[Action]:
        """Actual activation method. Override this.
        
        This should return an Action or None.
        If the activation is illegal, it should raise 
        an :class:`IllegalAbilityActivation` error.

        When overriding, you might want to use 
        `super().activate(**kwargs)` to avoid formatting this error. 

        Parameters
        ----------
        kwargs : dict
            Keyword arguments of the ability usage.

        Returns
        -------
        action : Action or None
            Resulting Action to put on the queue.

        Raises
        ------
        IllegalAbilityActivation
            If not `self.is_legal`.
        """
        if not self.is_legal(**kwargs):
            raise IllegalAbilityActivation(
                "Ability activation is not legal.", self, kwargs
            )
        return None

    def respond_to_event(self, event: Event) -> Optional[Action]:
        """Automatic response to TryActivateAbility events."""

        if isinstance(event, TryActivateAbility) and event.ability is self:
            kw = event.kwargs
            if not self.is_legal(**kw):
                return None
            return self.activate(**kw)
        return None


class IllegalAbilityActivation(MafiaError):
    """This ability activation was illegal."""

    def __init__(self, message, ability: ActivatedAbility = None, kw: dict = {}):
        super().__init__(message)
        self.ability = ability
        self.kw = dict(kw)

    def __str__(self):
        return "{}\nAttempted activation:\n{}.activate({})".format(
            super().__str__(),
            repr(self.ability),
            ", ".join("%s=%r" % v for v in self.kw.items()),
        )


class TriggeredAbility(Ability, Subscriber):
    """Triggered (passive) ability base class.

    To implement a triggered ability, :meth:`subscribe_to` 
    whatever triggers the ability in :meth:`__init__`, then 
    override :meth:`respond_to_event`.

    Attributes
    ----------
    owner : object
        The object that owns the ability.
    name : str
        Ability name (human-readable).
    """

    def __init__(self, owner, name: str):
        super().__init__(owner, name)
        # Add self.subscribe_to(YourEventHere)

    def respond_to_event(self, event: Event) -> Optional[Action]:
        """Override to respond to your event type.
        
        Parameters
        ----------
        event : Event
            The event that the EventManager is asking for a response to.
        
        Returns
        -------
        action : Action or None
            Response action, or None if none is required.
        """
        # check event type, make sure event.ability is self, then respond
        return None
