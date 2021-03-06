"""The core engine, to use as a context manager."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import AbstractContextManager
from typing import DefaultDict, List, Optional, Type, Union

from sortedcontainers import SortedList

from open_mafia_engine.util.repr import ReprMixin


class Event(ReprMixin):
    """Base event type."""


class Action(ABC, ReprMixin):
    """Base action.

    Attributes
    ----------
    owner : object
        TODO: Add owner or source or smth.
    priority : float
        The action priority for the queue. Default is 0.
    canceled : bool
        Whether the action was canceled (as a result of other actions).
    """

    def __init__(self, *, priority: float = 0, canceled: bool = False):
        self.priority = float(priority)
        self.canceled = bool(canceled)

    def __lt__(self, other: Action):
        if not isinstance(other, Action):
            return NotImplemented
        return self.priority > other.priority  # We sort decreasing by priority!

    @abstractmethod
    def __call__(self, game, context: ActionContext) -> None:
        """This executes the action.

        Parameters
        ----------
        game : GameState
            The current game state.
        context : ActionContext
            Queue and history of actions.
        """


EType = Type[Event]
AType = Type[Action]


class Subscriber(ABC):
    """Mixin for event subscription. Override `respond`."""

    @abstractmethod
    def respond(self, e: Event) -> Optional[Action]:
        """Delayed response to the Event with an Action (or None)."""
        return None

    def subscribe_current(self, *event_types: List[EType]):
        """Subscribes to the given event type(s) under current active engine."""
        engine = CoreEngine.current()
        engine.subscribe(self, *event_types)

    def __eq__(self, other):
        return other is self


class CoreEngine(AbstractContextManager):
    """Manages the game engine context."""

    __engines__ = []

    def __init__(self, subscriptions: DefaultDict[EType, List[Subscriber]] = None):
        self.subscriptions: DefaultDict[EType, List[Subscriber]] = defaultdict(list)
        if subscriptions is not None:
            for k, v in subscriptions.items():
                self.subscriptions[k].extend(v)

    def subscribe(self, obj: Subscriber, *event_types: List[EType]):
        """Subscribes the object to one or more events."""
        for et in event_types:
            if not issubclass(et, Event):
                raise TypeError(f"Expected Event subtype, got {et!r}")
            if obj not in self.subscriptions[et]:
                self.subscriptions[et].append(obj)

    def unsubscribe(self, obj: Subscriber, *event_types: List[EType]):
        """Unsubscribes the object to one or more events."""
        for et in event_types:
            if not issubclass(et, Event):
                raise TypeError(f"Expected Event subtype, got {et!r}")
            if obj in self.subscriptions[et]:
                self.subscriptions[et].remove(obj)

    def get_responses(self, e: Event) -> List[Action]:
        """Gets responses for all actions, in subscription order."""
        et: EType = type(e)
        res: List[Action] = []
        for obj in self.subscriptions[et]:
            x = obj.respond(e)
            if x is not None:
                res.append(x)
        return res

    @classmethod
    def current(cls) -> CoreEngine:
        """Returns the currently active engine. If there is none, raises ValueError."""
        if len(CoreEngine.__engines__) == 0:
            raise ValueError("No engine currently active.")
        return CoreEngine.__engines__[-1]

    def __repr__(self) -> str:
        cn = type(self).__qualname__
        e_count = len(self.subscriptions)
        s_count = sum(len(v) for v in self.subscriptions.values())
        return f"<{cn} with {e_count} events, {s_count} subs>"

    def __enter__(self) -> CoreEngine:
        CoreEngine.__engines__.append(self)
        return self

    def __exit__(self, exc_type=None, exc_value=None, tb=None) -> Optional[bool]:
        if (len(CoreEngine.__engines__) == 0) or (
            CoreEngine.__engines__[-1] is not self
        ):
            raise ValueError("Engine stack is corrupted!")
        CoreEngine.__engines__.pop()
        return super().__exit__(exc_type, exc_value, tb)


"""The default engine is here as a HACK/catch-all."""
default_engine = CoreEngine().__enter__()


class PreActionEvent(Event):
    """Occurs before an action starts to resolve."""

    def __init__(self, action: Action):
        self.action = action


class PostActionEvent(Event):
    """Occurs after an action resolves."""

    def __init__(self, action: Action):
        self.action = action


class ActionContext(object):
    """Context for actions and events, including a priority queue.

    Attributes
    ----------
    queue : List[Action]
        The list of enqueued actions.
        Ordering is by priority (desc) and time-of-action (implicitly ascending).
    history : List[Action]
        The history of actions that were taken.
    """

    def __init__(self, queue: List[Action] = None, history: List[Action] = None):
        self.queue = SortedList(queue)
        if history is None:
            history: List[Action] = []
        self.history = history

    def __repr__(self) -> str:
        cn = type(self).__qualname__
        return f"<{cn} with {len(self.queue)} queued, {len(self.history)} in history>"

    def enqueue(self, action: Union[Action, List[Action]]) -> None:
        """Enqueues one or more actions."""
        if isinstance(action, Action):
            self.queue.add(action)
        else:
            self.queue.update(action)

    def process(self, game_state):
        """Processes all the actions in the queue.

        Parameters
        ----------
        game : GameState
            The current state of the game.
        """

        while len(self.queue) > 0:
            self._process_next(game_state=game_state)

    def _process_next(self, game_state):
        """Processes the next actions (with the same priority) in the queue.

        This can cause additional actions (due to events), which will run in
        additional sub-contexts. Theoretically, this can lead to infinite
        recursion, so be careful!

        Parameters
        ----------
        game_state : GameState
            The current state of the game.
        """

        engine = CoreEngine.current()

        priority = self.queue[0].priority
        pre_responses: List[Action] = []
        actions: List[Action] = []
        post_responses: List[Action] = []

        while (len(self.queue) > 0) and (self.queue[0].priority == priority):
            action: Action = self.queue.pop(0)
            e_pre = PreActionEvent(action=action)

            actions.append(action)
            pre_responses += engine.get_responses(e_pre)

        pre_context = ActionContext(queue=pre_responses)
        pre_context.process(game_state=game_state)
        self.history += pre_context.history

        for action in actions:
            if not action.canceled:
                action(game_state, context=self)
                self.history.append(action)  # TODO: Maybe record in history anyways?

                e_post = PostActionEvent(action=action)
                post_responses += engine.get_responses(e_post)

        post_context = ActionContext(queue=post_responses)
        post_context.process(game_state=game_state)
        self.history += post_context.history


class CancelAction(Action):
    """Action that cancels another action."""

    def __init__(self, target: Action, *, priority: float = 0, canceled: bool = False):
        if not isinstance(target, Action):
            raise ValueError(f"Expected Action, got {target!r}")
        super().__init__(priority=priority, canceled=canceled)
        self.target = target

    def __call__(self, game_state, context: ActionContext) -> None:
        self.target.canceled = True
