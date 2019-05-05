"""Event system module for Mafia Engine.

NOTE: Description needs to be updated.

This engine is based on a publisher-:class:`Subscriber` event model. 
Whenever an :class:`Event` is set off, the :class:`EventManager` 
creates an :class:`ActionQueue` of responses (:class:`Action`'s), 
weighted by priority. This queue is then executed. Additional 
:class:`Event`'s that are set off during this execution form 
additional :class:`ActionQueue`'s.

There is currently no protection against infinite call/response, 
beyond the Python call stack overflowing...

:class:`Event`'s are split between :class:`ExternalEvent`'s (which 
are events that come from the API - the exact mechanism is TBD) 
and :class:`InternalEvent`'s, which are caused by other components 
(as a response to initial triggering events, for example).
"""

from mafia.util import ReprMixin
from collections.abc import MutableSequence
from typing import Optional, List
import functools
import logging


"""Active `EventManager` contexts."""
active_contexts = set()


class Event(ReprMixin):
    """Base class for all events."""


@functools.total_ordering
class Action(ReprMixin):
    """Base class for all actions.
    
    :class:`Action`'s are "stored" actions which can be executed. 
    Note that creating the object doesn't automatically execute - that has 
    to be called explicitly. In order to create custom behavior, you 
    only need to override :meth:`__init__` and :meth:`__execute__`.

    Comparison operations implemented for priority only.
    """

    def __execute__(self) -> bool:
        """Actually performs the action.

        Override this!

        This should also figure out whether the action should be 
        cancelled, explicitly (e.g. by other actions modifying 
        it) or implicitly (e.g. because the target is invalid).
        
        Returns
        -------
        success : bool
            Returns True if the action was completed.
        """
        return True

    @property
    def priority(self) -> float:
        """The priority of this action. Default is 0."""
        return 0

    def __eq__(self, other) -> bool:
        if not isinstance(other, Action):
            return NotImplemented
        return self.priority == other.priority

    def __lt__(self, other) -> bool:
        if not isinstance(other, Action):
            return NotImplemented
        return self.priority < other.priority


class ActionEvent(Event):
    """Event, related to an action. Base class."""

    def __init__(self, action: Action):
        if not isinstance(action, Action):
            raise TypeError(f"Expected Action, got {type(action)}")
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


class ActionQueue(MutableSequence):
    """Queue for Actions, sorting by priority value.
    
    This code isn't very efficient, O(N**2).
    """

    def __init__(self, items: list = []):
        self.items = self._prune_sort(items)

    @classmethod
    def _prune_sort(cls, items: List[Action]) -> List[Action]:
        """Filters out non-:class:`Action` items, sorts them by priority."""

        items = [i for i in items if isinstance(i, Action)]
        return sorted(items, reverse=True)

    def __getitem__(self, idx):
        return self.items[idx]

    def __delitem__(self, idx):
        del self.items[idx]

    def __setitem__(self, idx, value):
        self.items[idx] = value
        self.items = self._prune_sort(self.items)

    def __len__(self):
        return len(self.items)

    def insert(self, idx, value):
        self.items.append(value)
        self.items = self._prune_sort(self.items)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.items})"


class Subscriber(object):
    """Mixin that indicates object can act as a subscriber."""

    def respond_to_event(self, event: Event) -> Optional[Action]:
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
        return None

    def subscribe_to(self, *event_classes):
        """Subscribes self to multiple event classes (in context)."""
        global active_contexts
        for event_manager in active_contexts:
            event_manager.subscribe_me(self, *event_classes)

    def unsubscribe_from(self, *event_classes):
        """Unsubscribes self from multiple event classes (in context)."""
        global active_contexts
        for event_manager in active_contexts:
            event_manager.unsubscribe_me(self, *event_classes)


class EventManager(object):
    """Object that manages event-related things.

    Functions as a context manager
    
    Subscriptions:
    { EventType : set([subscribers]) }
    """

    def __init__(self):
        self.members = {}

    def __enter__(self):
        global active_contexts
        active_contexts.add(self)

    def __exit__(self, type, value, tb):
        global active_contexts
        try:
            active_contexts.remove(self)
        except KeyError:
            pass

    def subscribe_me(self, obj: Subscriber, *event_classes) -> None:
        """Subscribes `obj` to passed events.
        
        Parameters
        ----------
        obj : Subscriber
            Object to set as a subscriber.
        event_classes : list
            List of Event classes to subscribe to.
        """

        for event_class in event_classes:
            if event_class not in self.members:
                self.members[event_class] = set()
            self.members[event_class].add(obj)

    def unsubscribe_me(self, obj: Subscriber, *event_classes) -> None:
        """Removes `obj` from subscriptions for specific events.
        
        Currently doesn't look for parent classes of `event_classes.
        Probably should (so you could unsub from all Events 
        via the base class), but not implemented yet.

        Parameters
        ----------
        obj : Subscriber
            Object to set as a subscriber.
        event_classes : list
            List of Event classes to unsubscribe from.
        """

        # TODO: Unsubscribe from parent classes too?

        for event_class in event_classes:
            try:
                self.members[event_class].remove(obj)
            except KeyError:
                # could be error in members (no key 'event_class')
                # or could be error in the set (no key 'obj')
                # Maybe, warn that there was a subscription thing?
                pass

    def handle_event(self, event: Event) -> None:
        """Handles a passed event.
        
        Making a local action queue from subscriber actions, 
        then executes it. This may trigger more events!
        
        Parameters
        ----------
        event : Event
            Triggering event.
        """

        logging.debug(f"EM [Handling event: {event}]")

        # get set of subscribers (via isinstance())
        subscribers = []
        for event_class in self.members:
            if isinstance(event, event_class):
                new_subs = self.members[event_class]
                subscribers.extend(new_subs)

        # make local action queue
        q = ActionQueue()

        # call subscribers to add to local queue
        for sub in subscribers:
            act = sub.respond_to_event(event)
            if act is not None:
                q.append(act)

        # execute local queue
        for act in q:
            # send pre-event
            pae = PreActionEvent(self)
            self.handle_event(pae)

            # actually do it, and report success
            # To change behavior, override Action._execute()
            success = act.__execute__()
            if not success:
                return

            # send post-event
            poe = PostActionEvent(self)
            self.handle_event(poe)
