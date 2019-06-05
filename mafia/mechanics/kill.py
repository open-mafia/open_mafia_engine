"""Basic kill action mechanics.

"""


import typing
from mafia.core.event import Action, Event, Subscriber, PreActionEvent
from mafia.state.actor import Actor
from mafia.mechanics.prevent import PreventAction

# from mafia.core.ability import ActivatedAbility


class KillAction(Action):
    """Basic single-target kill action.

    Attributes
    ----------
    source : object
        The object performing the kill (usually, but not always,
        an :class:`Actor`).
    target : Actor
        The target being killed.
    canceled : bool
        Whether the action is canceled. Default is False.
    """

    def __init__(self, source, target: Actor, canceled: bool = False):
        if not isinstance(target, Actor):
            raise TypeError(f"Expected Actor, got {type(target)}.")
        super().__init__(canceled=canceled)
        self.source = source
        self.target = target

    def __execute__(self) -> bool:
        if self.canceled:
            return False

        self.target.status.alive = False
        return True


class KillPreventer(Subscriber):
    """Helper class that prevents kills on its target.
    
    Attributes
    ----------
    target : Actor
        The target that should be saved.
    """

    def __init__(self, target: Actor):
        if not isinstance(target, Actor):
            raise TypeError(f"Expected Actor, got {type(target)}.")
        self.target = target
        self.subscribe_to(PreActionEvent)

    def respond_to_event(self, event: Event) -> typing.Optional[Action]:
        """Responds to an event with an Action, or None.

        Override this!

        Parameters
        ----------
        event : Event
            The event you need to respond to.
        
        Returns
        -------
        None or Action
            The generated action to respond.
        """
        if isinstance(event, PreActionEvent):
            if isinstance(event.action, KillAction):
                if event.action.target == self.target:
                    return PreventAction(target=event.action)
        return None
