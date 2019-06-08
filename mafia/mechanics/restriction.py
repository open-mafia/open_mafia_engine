"""Various ability restrictions."""

import typing
from mafia.util import ReprMixin
from mafia.core.ability import Restriction, ActivatedAbility, TryActivateAbility
from mafia.state.game import PhaseState, PhaseChangeAction
from mafia.state.status import Status
from mafia.core.event import Subscriber, Event, Action, PostActionEvent


class StatusRestriction(Restriction):
    """Ability requires specific status conditions.

    Attributes
    ----------
    required : Status
        Required attribute values.
    owner : ActivatedAbility
        The ability that this restriction refers to.
    
    TODO
    ----
    Figure out how to set "required", "allowed", w/e conditions.
    """

    def __init__(
        self,
        required: typing.Mapping[str, object] = {},
        # allowed: typing.Optional[typing.Mapping[str, object]] = None,
        owner: ActivatedAbility = None,
    ):
        super().__init__(owner=owner)
        self.required = Status(**required)

    """
    @property
    def abil_owner(self):
        return self.owner.owner
    """

    def is_legal(self, ability: ActivatedAbility, **kwargs) -> bool:
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
        for key, stat in self.required.items():
            v2 = ability.owner.status.get(key, None)
            if (v2 is None) or (v2.value != stat.value):
                return False
        return True


def MustBeAlive() -> StatusRestriction:
    return StatusRestriction(required={"alive": True})


class PhaseUse(Restriction):
    """Allows use only in certain phases.
    
    Attributes
    ----------
    phase_state : PhaseState
        The phase state to check against.
    allowed_phases : list
        The phases when it is legal to use the ability.
    """

    def __init__(
        self,
        phase_state: PhaseState,
        allowed_phases: typing.List = [],
        owner: ActivatedAbility = None,
    ):
        super().__init__(owner=owner)
        self.phase_state = phase_state
        self.allowed_phases = list(allowed_phases)

    def is_legal(self, ability: ActivatedAbility, **kwargs) -> bool:
        if self.phase_state.current in self.allowed_phases:
            return True
        return False


class UseTracker(ReprMixin):
    """Object that tracks uses. Used in tandem with restrictions.

    Attributes
    ----------
    max_uses : int or None
        The maximum number of uses. Default is 1. 
        If None, there is no restriction.
    current_uses : int
        The current number of uses. Default is 0.
    can_use : bool
        Whether you can use it (i.e. False iff the max was reached).

    Actions
    -------
    IncrementUses - increments the count (at end of stack).
    ResetUses - resets the count (at end of stack).
    """

    def __init__(self, max_uses: typing.Optional[int] = 1, current_uses: int = 0):
        super().__init__()
        self.max_uses = max_uses
        self.current_uses = current_uses

    @property
    def can_use(self):
        """Returns False if the maximum has been reached."""
        if self.max_uses is None:
            return True
        return self.current_uses < self.max_uses

    class IncrementUses(Action):
        """Increments the use count of the parent restriction."""

        def __init__(self, tracker):
            if not isinstance(tracker, UseTracker):
                raise TypeError(f"Expected UseTracker, got {type(tracker)}")
            self.tracker = tracker

        @property
        def priority(self) -> float:
            """Minimum possible priority to always be at end of stack."""
            return float("-inf")

        def __execute__(self) -> bool:
            self.tracker.current_uses += 1
            return True

    def increment(self):
        """Returns an Action that increments self.current_uses."""
        return UseTracker.IncrementUses(self)

    class ResetUses(Action):
        """Resets the use count of the parent restriction."""

        def __init__(self, tracker):
            if not isinstance(tracker, UseTracker):
                raise TypeError(f"Expected UseTracker, got {type(tracker)}")
            self.tracker = tracker

        @property
        def priority(self) -> float:
            """Minimum possible priority to always be at end of stack."""
            return float("-inf")

        def __execute__(self) -> bool:
            self.tracker.current_uses = 0
            return True

    def reset(self):
        """Returns an Action that resets self.current_uses to 0."""
        return UseTracker.ResetUses(self)


class UseTrackerPerPhase(UseTracker, Subscriber):
    """Object that tracks uses, but resets with each phase. Used in tandem with restrictions.

    Attributes
    ----------
    max_uses : int or None
        The maximum number of uses. Default is 1. 
        If None, there is no restriction.
    current_uses : int
        The current number of uses. Default is 0.
    can_use : bool
        Whether you can use it (i.e. False iff the max was reached).

    Actions
    -------
    IncrementUses - increments the count (at end of stack).
    ResetUses - resets the count (at end of stack).
    """

    def __init__(self, max_uses: typing.Optional[int] = 1, current_uses: int = 0):
        super().__init__()
        self.subscribe_to(PostActionEvent)

    def respond_to_event(self, event: Event) -> typing.Optional[Action]:
        if isinstance(event, PostActionEvent):
            if isinstance(event.action, PhaseChangeAction):
                return self.reset()


class NUse(Restriction, Subscriber):
    """Allows limited number of uses.

    Attributes
    ----------
    tracker : UseTracker or None
        The tracking object to use. This can be shared with another restriction.
        If None, constructs one from the max_uses and current_uses arguments.
    max_uses : None or int
        Ignored if `tracker` is given.
        The maximum number of uses. If None, there is no restriction.
        Default is 1.
    current_uses : int
        Ignored if `tracker` is given.
        The current number of uses. Default is 0.

    Note
    ----
    This restriction listens to use attempts (:class:`TryActivateAbility`) 
    rather than checks for legality (:meth:`is_legal`) or successful uses.
    """

    def __init__(
        self,
        tracker: typing.Optional[UseTracker] = None,
        max_uses: typing.Optional[int] = 1,
        current_uses: int = 0,
        owner: ActivatedAbility = None,
    ):
        super().__init__(owner=owner)
        if tracker is None:
            tracker = UseTracker(max_uses=max_uses, current_uses=current_uses)
        self.tracker = tracker

        self.subscribe_to(TryActivateAbility)

    @property
    def max_uses(self):
        return self.tracker.max_uses

    @property
    def current_uses(self):
        return self.tracker.current_uses

    def respond_to_event(self, event: Event) -> typing.Optional[Action]:
        if isinstance(event, TryActivateAbility):
            if event.ability is self.owner:
                # If our owner ability is being used, we increment our use count
                # This will run at the end of all actions, so we increment at the end
                return self.tracker.increment()
        return None

    def is_legal(self, ability: ActivatedAbility, **kwargs) -> bool:
        return self.tracker.can_use
