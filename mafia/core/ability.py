"""Base classes for abilities.

An :class:`Ability` specifies the potential for an :class:`Actor` (or 
another object, such as a :class:`Game`) to perform an :class:`Action`. 

An :class:`ActivatedAbility` is activated by the actor directly, while 
a :class:`TriggeredAbility` is triggered by some external event. You can 
think of these as "active" and "passive/reactive" abilities respectively.
"""

import typing
from mafia.util import ReprMixin
from mafia.core.errors import MafiaError
from mafia.core.event import Action, Subscriber, Event


class Ability(ReprMixin):
    """Base class for all abilities.

    The `owner` is the object the ability belongs to. 
    It is usually, but not necessarily, an :class:`Actor`.
    
    Attributes
    ----------
    name : str
        Ability name (human-readable).
    owner : object
        The object that owns the ability.
    """

    def __init__(self, name: str, owner=None):
        super().__init__()
        self.name = name
        self.owner = owner


class AbilityAlreadyBound(MafiaError):
    """Ability has already been bound to another owner."""

    def __init__(self, ability, new_owner):
        msg = "Cannot add owner %r to ability %r, already has owner." % (
            new_owner,
            ability,
        )
        super().__init__(msg)
        self.ability = ability
        self.new_owner = new_owner


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


class Restriction(ReprMixin):
    """Ability restriction that prevents use. Base class.
    
    To subclass, override :meth:`__init__` and :meth:`is_legal`.

    Attributes
    ----------
    owner : ActivatedAbility
        The ability that this restriction refers to.
    """

    def __init__(self, owner: Ability = None):
        self.owner = owner

    def is_legal(self, ability: Ability, **kwargs) -> bool:
        """Check whether the ability usage is legal.

        This is used to pre-filter possible targets and improve 
        user experience (i.e. preventing impossible actions).
        Ideally, this is a lightweight operation.

        All restrictions are checked in the method 
        :meth:`ActivatedAbility.is_legal` 
        
        Parameters
        ----------
        ability : ActivatedAbility
            The ability you want to use.
        kwargs : dict
            Keyword arguments of the ability usage.

        Returns
        -------
        can_use : bool
            Whether the ability usage is legal, according to 
            this specific restriction (it may be illegal for 
            some other reason).
        """
        return True


class RestrictionAlreadyBound(MafiaError):
    """Restriction has already been bound to another owner."""

    def __init__(self, restriction, new_owner):
        msg = "Cannot add owner %r to restriction %r, already has owner." % (
            new_owner,
            restriction,
        )
        super().__init__(msg)
        self.restriction = restriction
        self.new_owner = new_owner


class ActivatedAbility(Ability, Subscriber):
    """Activated ability base class.

    To implement an activated ability, override 
    :meth:`activate`, with proper arguments, to return 
    the :class:`Action` (or `None`) to perform.

    Note that activate won't be called directly from the 
    code, but will instead be caused by an event. 
    
    Attributes
    ----------
    name : str
        Ability name (human-readable).
    owner : object
        The object that owns the ability.
    """

    def __init__(
        self, name: str, owner=None, restrictions: typing.List[Restriction] = []
    ):
        super().__init__(name=name, owner=owner)

        # Associate restrictions
        self.restrictions = []
        for r in restrictions:
            if r.owner is self:
                self.restrictions.append(r)
            elif r.owner is None:
                r.owner = self
                self.restrictions.append(r)
            else:
                raise RestrictionAlreadyBound(r, self)
        self.subscribe_to(TryActivateAbility)

    def is_legal(self, **kwargs) -> bool:
        """Check whether the ability usage is legal. Override this.

        Call :meth:`super().is_legal` when subclassing to auto-check restrictions.

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
        return all(r.is_legal(self, **kwargs) for r in self.restrictions)

    def activate(self, **kwargs) -> typing.Optional[Action]:
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

    def respond_to_event(self, event: Event) -> typing.Optional[Action]:
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
    name : str
        Ability name (human-readable).
    owner : object
        The object that owns the ability.
    """

    def __init__(self, name: str, owner=None):
        super().__init__(name=name, owner=owner)
        # Add self.subscribe_to(YourEventHere)

    def respond_to_event(self, event: Event) -> typing.Optional[Action]:
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
