"""Module that defines Action and related events."""

import logging

from mafia.core import GameObject
from mafia.core.event import InternalEvent, EventManager


class ActionEvent(InternalEvent):
    """Event, related to an action. Base class."""

    def __init__(self, action):
        self.action = action


class PreActionEvent(ActionEvent):
    """Event signifying that an action is about to begin.
        
    Attributes
    ----------
    action : Action
        The action that is attempted to be performed.
    """


class PostActionEvent(ActionEvent):
    """Event signifying an action has resolved.
    
    Attributes
    ----------
    action : Action
        The action that was performed.
    """


class Action(GameObject):
    """Base class for all actions.
    
    :class:`Action`'s are "stored" actions which can be executed. 
    Note that creating the object doesn't automatically :meth:`execute()` 
    it - that has to be called explicitly. The :class:`PreActionEvent` 
    and :class:`PostActionEvent` objects are created before and after the 
    action execution code runs - this allows responses to happen before 
    any changes are made. In order to create custom behavior, you 
    (probably) only need to override :meth:`_execute()`.
    """

    _default_priority = 0

    def __init__(self, priority=_default_priority):
        super().__init__()
        self.priority = priority

    def execute(self):
        """Runs the action, triggering events as needed.
        
        In most cases, to change the behavior, you only 
        need to override :meth:`_execute()`."""
                
        # send pre-event
        pae = PreActionEvent(self)
        EventManager.handle_event(pae)

        # actually do it, and report success
        # To change behavior, override Action._execute()
        success = self._execute()
        if not success:
            return

        # send post-event
        poe = PostActionEvent(self)
        EventManager.handle_event(poe)

    def _execute(self):
        """Actually performs the action, depending on parameters.

        Override this! Default action just sends to debug log.

        This should also figure out whether the action should be 
        cancelled, explicitly (e.g. by other actions modifying 
        it) or implicitly (e.g. because the target is invalid).
        
        Returns
        -------
        success : bool
            Returns True if the action was completed.
        """

        msg = "%s._execute()"
        args = self.__class__.__name__
        logging.getLogger(__name__).debug(msg, args)
        return True
