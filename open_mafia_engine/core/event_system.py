from __future__ import annotations
from abc import abstractmethod
from collections import defaultdict
from enum import Enum
import inspect
import logging
from typing import (
    Callable,
    DefaultDict,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)
from makefun import partial
from open_mafia_engine.core.game_object import GameObject
from open_mafia_engine.errors import MafiaBadHandler
from sortedcontainers.sortedlist import SortedList

if TYPE_CHECKING:
    from open_mafia_engine.core.game import Game

NoneType = type(None)

logger = logging.getLogger(__name__)


class ActionResolutionType(str, Enum):
    """How actions are resolved."""

    instant = "instant"
    end_of_phase = "end_of_phase"

    def __repr__(self):
        cn = type(self).__qualname__
        return f"{cn}({self.value!r})"


class Event(GameObject):
    """Core event object."""

    def __init__(self, game, /):
        super().__init__(game)


class _ActionEvent(Event):
    def __init__(self, game, action: Action, /):
        self._action = action
        super().__init__(game)

    @property
    def action(self) -> Action:
        return self._action


class EPreAction(_ActionEvent):
    """Pre-action event."""


class EPostAction(_ActionEvent):
    """Post-action event."""


class Action(GameObject):
    """Core action object.

    Attributes
    ----------
    priority : float
    canceled : bool
    """

    def __init__(self, game, /, *, priority: float = 0.0, canceled: bool = False):
        self._priority = float(priority)
        self._canceled = bool(canceled)
        super().__init__(game)

    @abstractmethod
    def doit(self):
        """Performs the action."""

    @property
    def priority(self) -> float:
        return self._priority

    @priority.setter
    def priority(self, v: float):
        v = float(v)
        # TODO - Event?
        self._priority = v

    @property
    def canceled(self) -> bool:
        return self._canceled

    @canceled.setter
    def canceled(self, v: bool):
        v = bool(v)
        # TODO - Event?
        self._canceled = v

    Pre = EPreAction
    Post = EPostAction

    def pre(self) -> EPreAction:
        """Get a pre-event for this action."""
        return self.Pre(self.game, self)

    def post(self) -> EPostAction:
        """Get a post-event for this action."""
        return self.Post(self.game, self)


class ActionQueue(GameObject):
    """Action queue.

    queue : List[Action]
        Actions are sorted by decreasing priority. Ties are broken by insertion order.
    history : List[Action]
        Actions are stored in the order they were processed in, including sub-queues.
    """

    MAX_DEPTH: int = 20

    def __init__(self, game, depth: int = 0):
        depth = int(depth)
        if depth > self.MAX_DEPTH:
            raise RecursionError(f"Reached recursion limit of {self.MAX_DEPTH}")
        self._depth = depth
        self._queue = SortedList([], key=self._action_sorter)
        self._history: List[Action] = []
        super().__init__(game)

    def __len__(self) -> int:
        return len(self._queue)

    @staticmethod
    def _action_sorter(action: Action) -> float:
        """Key function for sorting - by decreasing priority."""
        return -action.priority

    @property
    def depth(self) -> int:
        return self._depth

    @property
    def queue(self) -> List[Action]:
        return list(self._queue)

    @property
    def history(self) -> List[Action]:
        return list(self._history)

    def enqueue(self, action: Action):
        """Add an action to the queue."""
        if not isinstance(action, Action):
            raise TypeError(f"Expected Action, got {action!r}")
        self._queue.add(action)

    def pop_batch(self) -> List[Action]:
        """Gets the next batch of actions, removing them from the queue.

        If there are no more actions, this returns an empty list.
        """
        if len(self._queue) == 0:
            return []

        res = []
        priority = self._queue[0].priority
        while (len(self._queue) > 0) and (self._queue[0].priority == priority):
            action: Action = self._queue.pop(0)
            res.append(action)
        return res

    def peek_batch(self) -> List[Action]:
        """Peek at the next batch of actions, without removing them.

        If there are no more actions, this returns an empty list.
        """
        if len(self._queue) == 0:
            return []
        res = []
        i = 0
        priority = self._queue[0].priority
        while (i < len(self._queue)) and (self._queue[i].priority == priority):
            res.append(self._queue[i])
        return res

    def add_history(self, actions: List[Action]):
        """Adds the actions to history."""
        self._history.extend(actions)

    def __repr__(self) -> str:
        cn = type(self).__qualname__
        return f"<{cn} with {len(self._queue)} queued, {len(self._history)} in history>"

    def process_next_batch(self):
        next_batch: List[Action] = self.pop_batch()

        pre_responses = []
        for action in next_batch:
            pre_responses += self.game.event_engine.broadcast(action.pre())
        pre_queue = ActionQueue(self.game, depth=self._depth + 1)
        for pre_r in pre_responses:
            pre_queue.enqueue(pre_r)
        pre_queue.process_all()
        self.add_history(pre_queue.history)

        # Run the actions themselves
        for action in next_batch:
            if not action.canceled:
                action.doit()  # TODO
                self.add_history([action])

        # Get and run all post-action responses
        post_responses = []
        for action in next_batch:
            if not action.canceled:
                post_responses += self.game.event_engine.broadcast(action.post())
        post_queue = ActionQueue(self.game, depth=self._depth + 1)
        for post_r in post_responses:
            post_queue.enqueue(post_r)
        post_queue.process_all()
        self.add_history(post_queue.history)

    def process_all(self):
        while len(self) > 0:
            self.process_next_batch()


class Subscriber(GameObject):
    """Base class for objects that must listen to events.

    Creating Event Handlers
    -----------------------
    Subclass from this and use a `handler` or `handles` decorator:

        class MySub(Subscriber):
            @handles(Event)
            def handler_1(self, event: Event) ->
    """

    def __init__(self, game: Game, /):
        super().__init__(game)
        self._handler_funcs: List[_HandlerFunc] = []
        self._sub()

    def _sub(self):
        """Subscribe to events in the current game. This should happen automatically."""
        for handler in self.get_handlers():
            hf = self.game.event_engine.add_handler(handler, self)
            self._handler_funcs.append(hf)

    def _unsub(self):
        """Unsubscrive all handlers from the current game."""
        self.game.event_engine.remove_subscriber(self)

    @classmethod
    def get_handlers(cls) -> List[EventHandler]:
        """Returns all event handlers for this class."""
        res = []
        for T in cls.mro():
            for x in T.__dict__.values():
                if isinstance(x, EventHandler):
                    res.append(x)
        return res

    @property
    def handler_funcs(self) -> List[_HandlerFunc]:
        return list(self._handler_funcs)


_HandlerFunc = Callable[[Subscriber, Event], Optional[List[Action]]]


def _assert_legal_handler(func: _HandlerFunc):
    """Checks whether the function can be used as an event handler.

    Notes
    -----
    The logic for this is very complicated. Here are the basic ideas.

    - The bare signature (without annotations) should be `func(self, event)`
    - The names must be "self" and "event"!
    - Allowed annotations for "self":
        - `self` (empty)
        - `self: ST` where issubclass(ST, Subscriber)
    - Allowed annotations for "event":
        - `event` (empty)
        - `event: ET` where issubclass(ET, Event)
    - Allowed annotations for the return type:
        - `): ` (empty)
        - `: -> None` (no returned value)
        - `: -> List[AT]` where issubclass(AT, Action)
        - `: -> Optional[List[AT]]` where issubclass(AT, Action)
        - `: -> Union[List[AT1], List[AT2]]` where issubclass(AT#, Action)

    """

    # This should always work
    sig = inspect.signature(func)
    try:
        p_self, p_event = list(sig.parameters.values())
        assert p_self.name == "self"
        assert p_event.name == "event"
    except Exception as e:
        raise MafiaBadHandler(func) from e

    # This may not work, if import schenanigans occur
    try:
        type_hints = get_type_hints(func)
    except Exception:
        logger.exception("Could not get type hints for event handler:")
        return

    # Assuming typing worked, we can check these
    try:
        # Argument "self"
        # `self`, `self: SubscriberSubtype`
        th_self = type_hints.get("self")
        if th_self is not None:
            assert issubclass(th_self, Subscriber)

        # Argument "event"
        # `event`, `event: EventSubtype`, `event: Union[Event1, Event2]`
        th_event = type_hints.get("event")
        if th_event is None:
            # No type hints
            pass
        elif get_origin(th_event) is None:
            # `event: Event`
            assert issubclass(th_event, Event)
        elif get_origin(th_event) is Union:
            # `event: Union[Event1, Event2]`
            for arg in get_args(th_event):
                assert issubclass(arg, Event)
        else:
            raise TypeError(f"Bad typing hint for 'event': {th_event!r}")

        # Return Type
        # `: `, `-> None`, `: -> List[Action]`, `: -> Optional[List[Action]]`
        th_return = type_hints.get("return")
        if th_return in [None, NoneType]:
            # None or no return type
            pass
        elif get_origin(th_return) is None:
            # This might just be `Action`, for example
            raise TypeError(f"Must return None or List[Action], got {th_return!r}")
        elif get_origin(th_return) == list:
            # List[Action]
            for arg in get_args(th_return):
                assert issubclass(arg, Action)
        elif get_origin(th_return) == Union:
            # Optional[List[Action]] or Union[List[Action1], List[Action2]]
            for arg in get_args(th_return):
                if arg in [None, NoneType]:
                    pass
                elif get_origin(arg) == list:
                    for a2 in get_args(arg):
                        assert issubclass(a2, Action)
                else:
                    raise TypeError(f"Union contains unsupported arg: {arg!r}")
    except Exception as e:
        raise MafiaBadHandler(func) from e


class EventHandler(object):
    """Descriptor that implements event handling logic."""

    def __init__(self, func: _HandlerFunc, *etypes: List[Event]):
        _assert_legal_handler(func)
        self.func: _HandlerFunc = func
        self.etypes: List[Event] = list(etypes)

    def __set_name__(self, owner: Type[Subscriber], name: str):
        if not issubclass(owner, Subscriber):
            raise TypeError(f"Expected Subscriber, got {owner!r}")

        self.name = name

    def __get__(self, obj, objtype=None) -> Callable:
        # This returns the method that was wrapped
        return partial(self.func, obj)


def handler(func: _HandlerFunc) -> EventHandler:
    """Decorator to automatically infer event handler."""
    type_hints = get_type_hints(func)
    th = type_hints.get("event")
    if th is None:
        raise TypeError("Type hint for 'event' is required; otherwise, use `handles()`")
    if get_origin(th) is None:
        if issubclass(th, Event):
            return EventHandler(func, th)
    elif get_origin(th) is Union:
        etypes = get_args(th)
        for a in etypes:
            if not issubclass(a, Event):
                raise TypeError(f"One of Union types is not Event: {th!r}")
        return EventHandler(func, *etypes)
    raise NotImplementedError(f"Unsupported type hint: {th!r}")


def handles(*etypes: List[Event]) -> Callable[[_HandlerFunc], EventHandler]:
    """Decorator factory, to handle events.

    Usage
    -----

        class A(GameObject):
            @handles(Event)
            def f(self, event: Event) -> Optional[Action]:
                return None
    """

    def _inner(func: _HandlerFunc) -> EventHandler:
        return EventHandler(func, *etypes)

    return _inner


class EventEngine(GameObject):
    """Subscription and broadcasting engine."""

    def __init__(self, game: Game):
        self._handlers: DefaultDict[Type[Event], List[Callable]] = defaultdict(list)
        self._subscribers: DefaultDict[Type[Event], List[Subscriber]] = defaultdict(
            list
        )
        super().__init__(game)

    def add_handler(self, handler: EventHandler, parent: Subscriber) -> _HandlerFunc:
        """Adds the handler, with given parent, to own subscribers."""
        f = partial(handler.func, parent)
        for etype in handler.etypes:
            self._handlers[etype].append(f)

        if parent not in self._handlers[etype]:
            self._subscribers[etype].append(parent)
        return f

    # TODO: Unsubscription
    def remove_subscriber(self, sub: Subscriber):
        """Removes all subscriptions from the subscriber.

        FIXME: This operation is very hackish and iterates over EVERYTHING.
        This can probably be fixed by adding back-references, somehow.
        """
        hfs = sub.handler_funcs
        for etype in self._subscribers.keys():
            try:
                self._subscribers[etype].remove(sub)
                for hf in hfs:
                    try:
                        self._handlers[etype].remove(hf)
                    except ValueError:
                        pass
            except ValueError:
                pass
        sub._handler_funcs = []

    def broadcast(self, event: Event) -> List[Action]:
        """Broadcasts event to all handlers."""

        # Loop over superclasses, but make sure you don't repeat handlers
        funcs = []  # NOTE: not using a set, because we want deterministic sorting
        ET = type(event)
        for T in ET.mro():
            if issubclass(T, Event):
                funcs += [h for h in self._handlers[T] if h not in funcs]

        # Call each of the functions
        res = []
        for f in funcs:
            x = f(event)
            if x is None:
                x = []
            res.extend(x)
        return res
