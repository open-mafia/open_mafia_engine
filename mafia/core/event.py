""""""

from mafia.core import GameObject, singleton
from mafia.core.action import ActionQueue


class Event(GameObject):
    """Base class for all events."""


class ExternalEvent(Event):
    """Events from the API."""


class InternalEvent(Event):
    """Generated events."""


class Subscriber:
    """Represents an object that can act as a subscriber."""

    def respond_to_event(self, event):
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


@singleton
class EventManagerType:
    """Object that manages event-related things.
    
    Subscriptions:
    { EventType : set([subscribers]) }

    TODO: Rewrite with class-based singleton, not 
    as a decorator (ie. __new__...)
    """

    def __init__(self):
        self.members = {}

    def subscribe_me(self, obj, *event_classes):
        """Subscribes `obj` to passed events.
        
        Parameters
        ----------
        obj : GameObject
            Object to set as a subscriber.
        event_classes : list
            List of Event classes to subscribe to.
        """

        for event_class in event_classes:
            if event_class not in self.members:
                self.members[event_class] = set()
            self.members[event_class].add(obj)

    def unsubscribe_me(self, obj, *event_classes):
        """Removes `obj` from subscriptions for specific events.
        
        Currently doesn't look for parent classes of `event_classes.
        Probably should (so you could unsub from all Events 
        via the base class), but not implemented yet.

        Parameters
        ----------
        obj : GameObject
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

    def handle_event(self, event):
        """Handles a passed event.
        
        Making a local action queue from subscriber actions, 
        then executes it. This may trigger more events!
        
        Parameters
        ----------
        event : Event
            Triggering event.
        """

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
            q.add(act)

        # execute local queue
        q.execute()


EventManager = EventManagerType()
