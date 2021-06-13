from __future__ import annotations

import inspect
import logging
import warnings
from abc import abstractmethod
from collections import defaultdict
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    DefaultDict,
    Dict,
    List,
    Optional,
    Type,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from makefun import partial, wraps
from sortedcontainers import SortedList

from open_mafia_engine.core.game_object import GameObject
from open_mafia_engine.errors import MafiaBadHandler

if TYPE_CHECKING:
    from open_mafia_engine.core.game import Game

NoneType = type(None)

logger = logging.getLogger(__name__)


class Event(GameObject):
    """Core event object."""

    def __init__(self, game, /):
        super().__init__(game)


class _ActionEvent(Event):
    """Base class for pre- and post-action events."""

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
    game : Game
    source : GameObject
        The object that generated this action.
    priority : float
    canceled : bool

    Abstract Methods
    ----------------
    doit(self) -> None
        Performs the action.

    Class Attributes
    ----------------
    Pre : Type[EPreAction]
    Post : Type[EPostAction]
        Pre- and post-action event classes to use with `action.pre` and `action.post`.
        You may override these with your own when subclassing.
    """

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        *,
        priority: float = 0.0,
        canceled: bool = False,
    ):
        self._priority = float(priority)
        self._canceled = bool(canceled)
        if not isinstance(source, GameObject):
            raise TypeError(f"Expected GameObject, got {source!r}")
        self._source = source
        super().__init__(game)

    # NOTE: You can override these classes, even inline.
    Pre = EPreAction
    Post = EPostAction

    @abstractmethod
    def doit(self):
        """Performs the action."""

        # Override this.

    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        assert issubclass(cls.Pre, EPreAction)
        assert issubclass(cls.Post, EPostAction)

    @property
    def source(self) -> GameObject:
        return self._source

    @property
    def priority(self) -> float:
        return self._priority

    @priority.setter
    def priority(self, v: float):
        v = float(v)
        # You can add an event handler here
        self._priority = v

    @property
    def canceled(self) -> bool:
        return self._canceled

    @canceled.setter
    def canceled(self, v: bool):
        v = bool(v)
        # You can add an event handler here
        self._canceled = v

    def pre(self) -> EPreAction:
        """Create a pre-event for this action."""
        return self.Pre(self.game, self)

    def post(self) -> EPostAction:
        """Create a post-event for this action."""
        return self.Post(self.game, self)

    @classmethod
    def generate(
        cls, func: Callable, name: str = None, doc: str = None
    ) -> Type[Action]:
        """Create an Action subtype from a function.

        Parameters
        ----------
        func : Callable
            Function that does something. :)
        name : str
            What name to use. By default, will auto-generate a name from the func name.
        doc : str
            Docstring. By default, will use func doc, with prepended Action info.
        """

        if name is None:
            # NOTE: We can add random bits at the end to avoid conflicts
            # But this might mess up serialization?
            # from uuid import uuid4
            # rand_ = str(uuid4()).replace("-", "")[-8:]
            name = f"{cls.__name__}_{func.__name__}"

        if doc is None:
            doc = "(GENERATED ACTION) " + (func.__doc__ or "")

        # Get all signatures, parameters to merge
        sig_core = inspect.signature(cls.__init__)
        params_core = list(sig_core.parameters.values())
        sig_func = inspect.signature(func)
        params_func = list(sig_func.parameters.values())

        # Make sure the function has "self" as 0th arg
        if (len(params_func) < 1) or (params_func[0].name != "self"):
            raise TypeError(f"Function requires `self` argument to be first.")
        # Give a hint via warnings :)
        if params_func[0].annotation is None:
            warnings.warn(
                "We suggest you annotate like this to improve code editor experience:\n"
                f"  {func.__name__}(self: Action, ...)"
            )

        # Generate the list of params by merging
        DEFAULTS = {k: v.default for k, v in sig_core.parameters.items()}
        DEFAULTS.update({k: v.default for k, v in sig_func.parameters.items()})
        params_res: List[inspect.Parameter] = []
        attr_names = []
        kinds = [
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.VAR_KEYWORD,
        ]
        i_core = 0
        i_func = 0
        for kind in kinds:
            while (i_core < len(params_core)) and (params_core[i_core].kind == kind):
                params_res.append(params_core[i_core])
                i_core += 1
            while (i_func < len(params_func)) and (params_func[i_func].kind == kind):
                pfi = params_func[i_func]
                conflict_params = [p for p in params_res if p.name == pfi.name]
                if len(conflict_params) == 0:
                    params_res.append(pfi)
                    attr_names.append(pfi.name)
                elif len(conflict_params) == 1:
                    # conflict_params[0].default = pfi.default, except can't set param!
                    conf = conflict_params[0]
                    replacement = conf.replace(default=pfi.default)
                    params_res[params_res.index(conf)] = replacement
                    # don't add it - will conflict
                i_func += 1
        # Note: we make sure that we don't have duplicate *args, **kwargs
        sig_res = inspect.Signature(params_res)

        @wraps(cls.__init__, new_sig=sig_res)
        def __init__(
            self,
            game,
            /,
            *args,
            priority: float = DEFAULTS.get("priority", 0.0),
            canceled: bool = DEFAULTS.get("canceled", False),
            **kwargs,
        ):
            super(type(self), self).__init__(game, priority=priority, canceled=canceled)

            # Set attributes
            bs = sig_res.bind(
                self, game, *args, priority=priority, canceled=canceled, **kwargs
            )  # FIXME: Should we pass in `game`?
            bs.apply_defaults()
            for attr_name in attr_names:
                setattr(self, attr_name, bs.arguments[attr_name])
            # NOTE: We can't keep the signature, because someone might change
            # the arguments on the class instance; we have to "re-parse" instead

            # Housekeeping
            self._func = func
            self._sig = sig_res
            self._attr_names = tuple(attr_names)

        def doit(self):
            """Performs the action (generated from function)."""

            func = self._func
            sig = self._sig
            attr_names = self._attr_names

            # "re-parse" the signature
            args = []
            kwargs = {}
            for k, p in sig.parameters.items():
                if k not in attr_names:
                    continue
                v = getattr(self, k)
                if p.kind in [
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                ]:
                    args += v
                elif p.kind == inspect.Parameter.VAR_POSITIONAL:
                    args.extend(v)
                elif p.kind == inspect.Parameter.KEYWORD_ONLY:
                    kwargs[k] = v
                elif p.kind == inspect.Parameter.VAR_KEYWORD:
                    kwargs.update(v)

            func(self, *args, **kwargs)

        GeneratedAction = type(
            name, (cls,), {"__init__": __init__, "doit": doit, "__doc__": doc}
        )
        return GeneratedAction


class CancelAction(Action):
    """Action that cancels other actions."""

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        target: Action,
        *,
        priority: float = 50.0,
        canceled: bool = False,
    ):
        self._target = target
        super().__init__(game, source, priority=priority, canceled=canceled)

    @property
    def target(self) -> Action:
        return self._target

    @target.setter
    def target(self, v: Action):
        if not isinstance(v, Action):
            raise TypeError(f"Can only cancel Actions, but got {v!r}")
        self._target = v

    def doit(self):
        self.target.canceled = True


class ConditionalCancelAction(CancelAction):
    """Cancels the action, but checks `condition` just in case again.

    If `condition(action)`, actually does cancel the action.
    """

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        target: Action,
        condition: Callable[[Action], bool],
        *,
        priority: float = -100,
        canceled: bool = False,
    ):
        self._condition = condition
        super().__init__(game, source, target, priority=priority, canceled=canceled)

    @property
    def condition(self) -> Callable[[Action], bool]:
        return self._condition

    def doit(self):
        if self.condition(self.target):
            super().doit()


class ActionInspector(object):
    """Helper to inspect Action objects."""

    def __init__(self, action: Action):
        self._action = action

    @property
    def action(self) -> Action:
        return self._action

    @property
    def ignored_args(self) -> List[str]:
        """Arguments that are ignored"""
        return ["self", "game", "priority", "canceled", "return"]

    @property
    def type_hints(self) -> Dict[str, Type]:
        """Type hints, without ignored arguments."""
        raw = get_type_hints(self.action.__init__)
        return {k: v for k, v in raw.items() if k not in self.ignored_args}

    @property
    def param_names(self) -> List[str]:
        """Parameter names."""
        return list(self.type_hints.keys())

    def params_of_type(self, T: Type) -> List[str]:
        """Returns parameter names that have the given type."""

        def chk(v):
            try:
                return issubclass(v, T)
            except Exception:
                return False

        return [k for k, v in self.type_hints.items() if chk(v)]

    def values_of_type(self, T: Type) -> Dict[str, Any]:
        return {k: self.extract_value(k) for k in self.params_of_type(T)}

    def extract_value(self, param: str) -> Any:
        """Gets value for the parameter."""
        # TODO: Make this smarter? :)
        return getattr(self.action, param)

    def set_value(self, param: str, obj: Any):
        """Sets value for the parameter."""
        # TODO: Make this smarter? :)
        if not hasattr(self.action, param):
            warnings.warn(f"Action has no parameter {param!r}, setting anyways.")
        return setattr(self.action, param, obj)


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
                action.doit()
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
    """Base class for objects that listen to events.

    Creating Event Handlers
    -----------------------
    Subclass from this and use a `handler` or `handles` decorator.
    The following result in the same calls behavior:

        class MySub(Subscriber):
            @handles(EPreAction)
            def handler_1(self, event) -> Optional[List[Action]]:
                return None

            @handler
            def handler_2(self, event: EPreAction):
                return []

    Adding Constraints
    ------------------
    `Constraint`s are added after the Subscriber is created.
    """

    def __init__(self, game: Game, /, *, use_default_constraints: bool = True):
        self._use_default_constraints = bool(use_default_constraints)
        super().__init__(game)
        self._constraints: List[Constraint] = []
        self._handler_funcs: List[_HandlerFunc] = []
        self._sub()
        if self._use_default_constraints:
            self.add_default_constraints()

    @property
    def constraints(self) -> List[Constraint]:
        return list(self._constraints)

    @property
    def use_default_constraints(self) -> bool:
        """Whether this object is using default constraints for this class."""
        return self._use_default_constraints

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

    def add_default_constraints(self):
        """Adds default constraints for this type. Override for your own types."""

        # Nothing here for default subscribers :)

    def check_constraints(self, action: Action) -> List[Constraint.Violation]:
        """Checks all constraints. All violations are returned."""
        res = []
        for con in self._constraints:
            r = con.check(action)
            if r is not None:
                res.append(r)
        return res


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

        @wraps(func)
        def wrapped(self: Subscriber, event: Event) -> Optional[List[Action]]:
            # Wrap the function to check constraints.
            raw = func(self, event)
            if raw is None:
                return None
            # TODO: Maybe allow just returning Action or Optional[Action]?
            # That would simplify many handler functions that return just 1 Action.
            # But I'd have to rewrite _assert_legal_handler() ... :P
            if not isinstance(raw, list):
                raise TypeError(f"Expected List[Action], got {raw!r}")
            res = []
            for action in raw:
                violations = self.check_constraints(action)
                if len(violations) == 0:
                    res.append(action)
                else:
                    msg = [f"Constraint Violations for {type(action).__qualname__}:"]
                    msg += [f"  {v.msg}" for v in violations]
                    logger.warning("\n".join(msg))
            return res

        self.func: _HandlerFunc = wrapped  # func
        self.etypes: List[Event] = list(etypes)

    def __set_name__(self, owner: Type[Subscriber], name: str):
        if not issubclass(owner, Subscriber):
            raise TypeError(f"Expected Subscriber, got {owner!r}")

        self.name = name

    def __get__(self, obj: Subscriber, objtype=None) -> Callable:
        # This returns the method that was wrapped

        return partial(self.func, obj)
        # return partial(wrapped, obj)


def handler(func: _HandlerFunc) -> EventHandler:
    """Decorator to automatically infer event handler.

    Usage
    -----
    Use this as a decorator with a mandatory type hint for `event`:

        class A(Subscriber):
            @handler
            def f(self, event: Union[EPreAction, EPostAction]):
                return []
    """

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
    Use this as a decorator factory with the event types as arguments:

        class A(Subscriber):
            @handles(EPreAction, EPostAction)
            def f(self, event) -> Optional[List[Action]]:
                return None
    """

    def _inner(func: _HandlerFunc) -> EventHandler:
        return EventHandler(func, *etypes)

    return _inner


class Constraint(Subscriber):
    """Base class for constraints.

    Override `check` and return a `self.Violation("Description")` or `None`.

    Note that each Constraint is itself a Subscriber, so it technically can have
    its own constraints, but by default they're not used.
    """

    def __init__(self, game, /, parent: Subscriber):
        self._parent = parent
        super().__init__(game, use_default_constraints=False)
        self._parent._constraints.append(self)  # FIXME: How do we remove constraints?

    @property
    def parent(self) -> Subscriber:
        return self._parent

    class Violation(object):
        """Constraint was violated."""

        def __init__(self, msg: str) -> None:
            self._msg = str(msg)

        @property
        def msg(self) -> str:
            return self._msg

        def __repr__(self) -> str:
            cn = type(self).__qualname__  # e.g. "Constraint.Violation"
            return f"{cn}({self.msg!r})"

    @abstractmethod
    def check(self, action: Action) -> Optional[Constraint.Violation]:
        """Checks whether the `action` is allowed.

        If allowed, return None.
        If not allowed, return a `Constraint.Violation`
        """

    def hook_pre_action(self, action: Action) -> Optional[List[Action]]:
        """Hook called when parent is trying to action & no violation for self."""

    def hook_post_action(self, action: Action) -> Optional[List[Action]]:
        """Hook called when parent successfully actioned."""

    @handler
    def handler_pre(self, event: EPreAction) -> Optional[List[Action]]:
        if isinstance(event, EPreAction) and event.action.source == self.parent:
            violation = self.check(event.action)
            if violation is None:
                return self.hook_pre_action(event.action)
            # we have a violation - cancel!
            return [CancelAction(self.game, self, target=event.action)]

    @handler
    def handler_post(self, event: EPostAction) -> Optional[List[Action]]:
        if isinstance(event, EPostAction) and event.action.source == self.parent:
            return self.hook_post_action(event.action)


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
