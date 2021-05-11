from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
import logging
from typing import Any, Dict, List, MutableMapping, Optional, Tuple, Type, Union

from sortedcontainers import SortedList

from open_mafia_engine.util.repr import ReprMixin


logger = logging.getLogger(__name__)


class GameObject(ReprMixin, ABC):
    """Core game object."""


class Event(GameObject):
    """Represents some event."""

    @classmethod
    def default_code(cls) -> str:
        """Gets the hierarchy code for this event type."""
        # NOTE: MRO may be broken due to ABC?...
        # return cls.__qualname__
        mro = cls.mro()
        parts = []
        for x in mro:
            parts.append(x.__qualname__)
            if x is Event:
                break
        return ":".join(reversed(parts))

    def code(self) -> str:
        """Gets the code for this particular event."""
        return self.default_code()


ETypeOrS = Union[Type[Event], str]


def normalize_etype(etype: ETypeOrS) -> str:
    """Normalizes event type to a string."""

    if isinstance(etype, str):
        pass
    elif issubclass(etype, Event):
        etype: Type[Event]
        etype: str = etype.default_code()
    else:
        raise TypeError(f"Expected str or Event subclass, got {etype!r}")
    return etype


class Action(GameObject):
    """Some action.

    Attributes
    ----------
    source : GameObject
    priority : float
        Higher priority means it should be executed first.
    """

    def __init__(
        self, source: GameObject, *, priority: float = 0, canceled: bool = False
    ):
        self._source = source
        self._priority = float(priority)
        self._canceled = bool(canceled)

    @abstractmethod
    def doit(self, game: Game) -> None:
        """Runs the action."""
        raise NotImplementedError(f"doit() not implemented for {self!r}")

    @property
    def source(self) -> GameObject:
        return self._source

    @property
    def priority(self) -> float:
        return self._priority

    @property
    def canceled(self) -> bool:
        return self._canceled

    @canceled.setter
    def canceled(self, value):
        self._canceled = bool(value)

    def __lt__(self, other: Action):
        if not isinstance(other, Action):
            return NotImplemented
        return self._priority > other._priority  # We sort decreasing by priority!


class EPreAction(Event):
    """Pre-action event, triggered before an action is about to occur."""

    def __init__(self, action: Action):
        self._action = action

    @property
    def action(self) -> Action:
        return self._action

    def code(self) -> str:
        return self.default_code() + ":" + type(self._action).__qualname__


class EPostAction(Event):
    """Post-action event, triggered when the action has already occurred."""

    def __init__(self, action: Action):
        self._action = action

    @property
    def action(self) -> Action:
        return self._action

    def code(self) -> str:
        return self.default_code() + ":" + type(self._action).__qualname__


class Subscriber(GameObject):
    """Mixin class for objects that need to recieve event broadcasts."""

    def __subscribe__(self, game: Game) -> None:
        """Subscribe to some particular event type(s)."""

    def respond_to_event(self, event: Event, game: Game) -> Optional[Action]:
        """Respond to an event, given the game context."""
        return None


class Alignment(GameObject):
    """A 'team' of Actors.

    Attributes
    ----------
    game : Game
    name : str
    actors : List[Actor]

    TODO: Add wincons.
    """

    def __init__(self, game: Game, name: str, actors: List[Actor] = None):
        if actors is None:
            actors = []
        self.name = name
        self._actors = list(actors)

        # Register self with the parent game
        self._game = game
        self._game._alignments.append(self)

    @property
    def game(self) -> Game:
        return self._game

    def add_actor(self, actor: Actor):
        if actor not in self._actors:
            self._actors.append(actor)
            actor.add_alignment(self)

    def remove_actor(self, actor: Actor):
        if actor in self._actors:
            self._actors.remove(actor)
            actor.remove_alignment(self)

    @property
    def actors(self) -> List[Actor]:
        return list(self._actors)


class Status(GameObject, MutableMapping):
    """dict-like representation of an actor's status.

    Access of empty attribs gives None.
    Changing an attribute emits an EStatusChange event.

    Attributes
    ----------
    parent: Actor
    attribs : dict
        Raw keyword arguments for the status.
    """

    def __init__(self, parent: Actor, **attribs: Dict[str, Any]):
        self._parent = parent
        self._attribs = attribs

    @property
    def game(self) -> Game:
        return self._parent.game  # == self._parent._game

    @property
    def parent(self) -> Actor:
        return self._parent

    @property
    def attribs(self) -> Dict[str, Any]:
        return dict(self._attribs)

    def __getitem__(self, key) -> Any:
        return self._attribs.get(key, None)

    def __delitem__(self, key) -> None:
        old_val = self[key]
        if old_val is not None:
            del self._attribs[key]
        if old_val is None:  # TODO: Maybe broadcast always?
            return
        self.game.process_event(EStatusChange(self, key, old_val, None))

    def __setitem__(self, key, value) -> None:
        old_val = self[key]
        self._attribs[key] = value
        if old_val == value:  # TODO: Maybe broadcast always?
            return
        self.game.process_event(EStatusChange(self, key, old_val, value))

    def __len__(self) -> int:
        return len(self._attribs)

    def __iter__(self):
        return iter(self._attribs)


class EStatusChange(Event):
    """The Status has changed for some Actor."""

    def __init__(self, status: Status, key: str, old_val: Any, new_val: Any):
        self._status = status
        self._key = key
        self._old_val = old_val
        self._new_val = new_val

    @property
    def status(self) -> Status:
        return self._status

    @property
    def actor(self) -> Actor:
        return self.status.parent

    @property
    def key(self) -> str:
        return self._key

    @property
    def old_val(self) -> Any:
        return self._old_val

    @property
    def new_val(self) -> Any:
        return self._new_val

    def code(self) -> str:
        return self.default_code() + ":" + type(self._action).__qualname__


class Actor(GameObject):
    """Represents a person or character.

    Attributes
    ----------
    game : Game
    name : str
    alignments : List[Alignment]
    abilities : List[Ability]
    """

    def __init__(
        self,
        game: Game,
        name: str,
        alignments: List[Alignment] = None,
        abilities: List[Ability] = None,
        status: Dict[str, Any] = None,
    ):
        if abilities is None:
            abilities = []
        if alignments is None:
            alignments = []
        if status is None:
            status = {}

        self.name = name

        # Register self with the parent game
        self._game = game
        self._game._actors.append(self)

        # Add self to "parent" alignments
        self._alignments = list(alignments)
        for al in self._alignments:
            al.add_actor(self)

        self._abilities = list(abilities)
        self._status = Status(self, **status)

    @property
    def game(self) -> Game:
        return self._game

    @property
    def status(self) -> Status:
        return self._status

    @property
    def alignments(self) -> List[Alignment]:
        return list(self._alignments)

    @alignments.setter
    def alignments(self, new_alignments: List[Alignment]):
        """Changing alignments - remove self from old ones, add to new ones."""
        to_del = [a for a in self._alignments if a not in new_alignments]
        to_add = [a for a in new_alignments if a not in self._alignments]
        for al in to_del:
            al.remove_actor(self)
        for al in to_add:
            al.add_actor(self)
        self._alignments = list(new_alignments)  # technically not needed

    def add_alignment(self, al: Alignment):
        """Adds an alignment to this Actor."""
        if al not in self._alignments:
            self._alignments.append(al)
            al.add_actor(self)

    def remove_alignment(self, al: Alignment):
        """Removes an alignment from this Actor."""
        if al in self._alignments:
            self._alignments.remove(al)
            al.remove_actor(self)

    @property
    def abilities(self) -> List[Ability]:
        return list(self._abilities)

    def remove_ability(self, ability: Ability):
        """Removes the ability entirely."""
        if ability in self._abilities:
            self._abilities.remove(ability)
            del ability

    def take_control_of_ability(self, ability: Ability):
        """Moves the ability to this owner."""
        if ability not in self._abilities:
            ability.owner = self


class Ability(Subscriber):
    """An Ability is a part of the role that allows some sort of action.

    This is a base class. If you need to be able to "activate" your ability, then use
    the ActivatedAbility class. If you want a "triggered" ability, then override
    `__subscribe__()` and `respond_to_event()` with the relevant events.

    Attributes
    ----------
    owner : Actor
        Abilities must always have an owner that points back at them.
    name : str
    constraints : List[Constraint]
        Constraints on ability usage.
    """

    def __init__(self, owner: Actor, name: str, constraints: List[Constraint] = None):
        if constraints is None:
            constraints = []
        self.name = name

        # Set the owner
        self._owner = owner
        self._owner._abilities.append(self)

        self._constraints = list(constraints)
        for c in constraints:
            self.take_control_of_constraint(c)

        # Auto-subscribe
        self.__subscribe__(self.game)

    def clone(self, new_owner: Actor) -> Ability:
        """Clones this ability with a new owner."""
        raise NotImplementedError("TODO: Implement")

    @property
    def game(self) -> Game:
        return self.owner.game

    @property
    def owner(self) -> Actor:
        return self._owner

    @owner.setter
    def owner(self, new_owner: Actor):
        """Changing owner - should remove self from the old one."""
        self._owner._abilities.remove(self)
        self._owner = new_owner
        self._owner._abilities.append(self)

    @property
    def constraints(self) -> List[Constraint]:
        return list(self._constraints)

    def remove_constraint(self, constraint: Constraint):
        if constraint in self._constraints:
            self._constraints.remove(constraint)
            del constraint

    def take_control_of_constraint(self, constraint: Constraint):
        if constraint not in self._constraints:
            constraint.parent = self


class EActivateAbility(Event):
    """Event of intent to activate an ability.

    Attributes
    ----------
    ability : ActivatedAbility
        The ability to activate. Type matters!
    params : dict
        Keyword arguments of parameters. Check the signature of `ability`.
    """

    def __init__(self, ability: ActivatedAbility, **params: Dict[str, Any]):
        self._ability = ability
        self._params = dict(params)

    @property
    def ability(self) -> ActivatedAbility:
        return self._ability

    @property
    def params(self) -> Dict[str, Any]:
        return dict(self._params)

    def code(self) -> str:
        return self.code_for(type(self._ability))

    @classmethod
    def code_for(cls, atype: Type[Ability]) -> str:
        return cls.default_code() + ":" + atype.__qualname__

    def __repr__(self):
        cn = type(self).__qualname__
        kv = ", ".join(
            [f"ability={self._ability!r}"]
            + [f"{k}={v!r}" for k, v in self._params.items()]
        )
        return f"{cn}({kv})"


class ActivatedAbility(Ability):
    """Ability that is activated by the `EActivateAbility` event.

    Override `make_action` for your custom abilities.

    Alternatively, use the "template" to make a simple action-creating ability.
    The following are equivalent (using the default name for the second):

        MyAbility = ActivatedAbility.create_type(MyAction, name="MyAbility")
        ActivateAbility_MyAction = ActivatedAbility[MyAction]
    """

    @abstractmethod
    def make_action(self, game: Game, **params) -> Optional[Action]:
        raise NotImplementedError(f"No `make_action` for {self!r}")

    def __subscribe__(self, game: Game) -> None:
        game.add_sub(self, EActivateAbility.code_for(type(self)))

    def respond_to_event(self, event: Event, game: Game) -> Optional[Action]:
        if isinstance(event, EActivateAbility):
            if event.ability is self:
                params = event.params
                for con in self.constraints:
                    if not con.is_ok(game, **params):
                        return None
                return self.make_action(game=game, **params)
        return None

    @classmethod
    def create_type(
        cls, atype: Type[Action], name: str = None
    ) -> Type[ActivatedAbility]:
        """Dynamically creates an ability type from the action.

        Parameters
        ----------
        atype : type
            Subclass of Action.
        name : str
            The name of the type. If not given, generates one from the action type.
        """

        if not issubclass(atype, Action):
            raise TypeError(f"Expected subclass of Action, got {atype!r}")
        if name is None:
            name = f"{cls.__qualname__}_{atype.__qualname__}".replace(".", "_")

        # TODO: Maybe copy the signature from `atype` via the `inspect` module? :)

        def make_action(self, game: Game, **params) -> Optional[Action]:
            return atype(source=self, **params)

        _GeneratedClass = type(name, (cls,), {"make_action": make_action})

        return _GeneratedClass

    def __class_getitem__(cls, atype: Type[Action]) -> Type[ActivatedAbility]:
        return cls.create_type(atype=atype)


class Constraint(GameObject):
    """A constraint on the use of particular abilities.

    parent : Ability
        The parent ability.
    """

    def __init__(self, parent: Ability):
        self._parent = parent
        self._parent._constraints.append(self)

    @abstractmethod
    def is_ok(self, game: Game, **params: Dict[str, Any]) -> bool:
        """Checks whether it is OK to make the action.

        Overwrite this. Remember that `self.parent` is also available.
        """
        return True

    @property
    def game(self) -> Game:
        return self._parent.game  # == self._parent._owner.game

    @property
    def parent(self) -> Ability:
        return self._parent

    @parent.setter
    def parent(self, new_parent: Ability):
        """Changing parent."""
        self._parent._constraints.remove(self)
        self._parent = new_parent
        self._parent._constraints.append(self)


class ActionResolutionType(str, Enum):
    """When actions are resolved."""

    instant = "instant"
    end_of_phase = "end_of_phase"


class Phase(GameObject):
    """Represents a monolithic "phase" of action.

    Attributes
    ----------
    name : str
        The current phase name.
    action_resolution : ActionResolutionType
        One of {"instant", "end_of_phase"}
    """

    def __init__(
        self,
        name: str,
        action_resolution: Union[
            str, ActionResolutionType
        ] = ActionResolutionType.instant,
    ):
        self.name = name
        self.action_resolution = ActionResolutionType(action_resolution)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Phase):
            return NotImplemented
        return (o.name == self.name) and (o.action_resolution == self.action_resolution)


class EPhaseEnd(Event):
    """The current phase is about to end.

    This will force the Game's action queue to process the whole queue.
    Note that you can always get the current phase from the Game object.
    """


class EPhaseStart(Event):
    """The next phase has just started.

    Note that you can always get the current phase from the Game object.
    """


class PhaseCycle(GameObject):
    """Simple phase cycle."""

    def __init__(self, phases: List[Phase], num: int = 0):
        if (not isinstance(num, int)) or (num < 0):
            raise TypeError(f"num must be a nonnegative int, got {num!r}")
        self._phases = phases
        self._num = num

    @property
    def current(self) -> Phase:
        return self._phases[self._num % len(self._phases)]

    @property
    def phases(self) -> List[Phase]:
        return list(self._phases)

    @property
    def num(self) -> int:
        return self._num

    @num.setter
    def num(self, v: int):
        """Sets the phase number."""

        if not isinstance(v, int):
            raise TypeError(f"num must be an int, got {v!r}")
        if v < self._num:
            raise ValueError(f"Attempted to decrease phase: {v} < {self._num}")
        elif v == self._num:
            return  # ignore
        # otherwise, we will advance to `v`
        print("TODO: EPhaseEnd")
        self._num = v
        print("TODO: EPhaseStart")

    def advance_to(self, phase: Union[int, str, Phase]):
        """Advances to the given phase, skipping those between.

        If `phase` is an int, it does the same as setting `self.num = phase`.
        If `phase` is a string or Phase, it matches the *next* phase that matches
        (i.e. it always advances).
        """
        N = len(self._phases)

        if isinstance(phase, int):
            self.num = phase  #
            return
        elif isinstance(phase, str):
            pname = phase

            if pname == self.current.name:
                return  # ignore
            found_ph = [(i, p) for i, p in enumerate(self.phases) if p.name == pname]
            if len(found_ph) == 0:
                raise ValueError(f"No phase with name {pname!r} found in {self.phases}")
            elif len(found_ph) > 1:
                raise ValueError(f"Ambiguous phase names: {found_ph}")
            i, phase = found_ph[0]
        elif isinstance(phase, Phase):
            found_ph = [(i, p) for i, p in enumerate(self.phases) if p == phase]
            if len(found_ph) == 0:
                raise ValueError(f"Phase {phase!r} not found in {self.phases}")
            elif len(found_ph) > 1:
                raise ValueError(f"Ambiguous phase names: {found_ph}")
            i, phase = found_ph[0]
        else:
            raise TypeError(f"Expected int, str or Phase, got {phase!r}")

        # We have i, but we need to advance to the next
        j = self._num % N
        forward = (i - j) % N
        if forward == 0:  # same phase - add N
            forward += N
        self.num = self._num + forward

    def __next__(self) -> Phase:
        self.num += 1
        return self.current

    @classmethod
    def make_day_night(cls) -> PhaseCycle:
        """Makes the default day/night cycle."""

        return cls(
            phases=[
                Phase(name="day", action_resolution=ActionResolutionType.instant),
                Phase(
                    name="night", action_resolution=ActionResolutionType.end_of_phase
                ),
            ]
        )


class _EventEngine(ReprMixin):
    """Runs event logic. Base class for Game."""

    def __init__(self, *, subscribers: Dict[str, List[Subscriber]] = None):
        # Fix arguments
        if subscribers is None:
            subscribers = {}

        # Initialize subscribers
        self._subscribers = defaultdict(list, subscribers)

    @property
    def subscribers(self) -> Dict[str, List[Subscriber]]:
        return {k: v for k, v in self._subscribers.items() if len(v) > 0}

    def add_sub(self, sub: Subscriber, *etypes: Tuple[ETypeOrS, ...]) -> None:
        """Subscribes `sub` to one or more event types."""

        for etype in etypes:
            etype = normalize_etype(etype)
            if sub not in self._subscribers[etype]:
                self._subscribers[etype].append(sub)

    def remove_sub(self, sub: Subscriber, *etypes: Tuple[ETypeOrS, ...]) -> None:
        """Unsubscribes `sub` from one or more event types."""

        for etype in etypes:
            etype = normalize_etype(etype)
            try:
                self._subscribers[etype].remove(sub)
            except ValueError:
                logger.warn(f"Attempted to remove sub from unsubbed {etype!r}")

    def broadcast_event(self, event: Event) -> List[Action]:
        """Broadcasts an event to all relevant subscribers."""

        parts = event.code().split(":")

        affected_subs: List[Subscriber] = []
        for i in range(len(parts) + 1):  # including "" and `event.code()`
            subs_i = self._subscribers[":".join(parts[:i])]
            affected_subs += [s for s in subs_i if s not in affected_subs]

        res = []
        for sub in affected_subs:
            response = sub.respond_to_event(event=event, game=self)
            if response is not None:
                res.append(response)
        return res


class ActionQueue(GameObject):
    """Queue for properly ordering and executing actions.

    Attributes
    ----------
    queue : List[Action]
        These actions are queued to be executed. First actions have higher priority.
    history : List[Action]
        These actions have already been executed, and are here just for information.
    depth : int
        This is the recursion depth, limited by `ActionQueue.max_depth`.
        You usually don't need to set this by hand.
    """

    max_depth: int = 20

    def __init__(
        self,
        queue: List[Action] = None,
        history: List[Action] = None,
        *,
        depth: int = 0,
    ):
        if depth > self.max_depth:
            raise RecursionError(f"Reached recursion limit of {self.max_depth}")
        if queue is None:
            queue = []
        if history is None:
            history = []

        self._queue = SortedList(queue)
        self._history = list(history)
        self._depth = depth

    @property
    def depth(self) -> int:
        return int(self._depth)

    @property
    def history(self) -> List[Action]:
        """Historic actions are read-only."""
        return list(self._history)

    @property
    def queue(self) -> List[Action]:
        """A view of the queue in its current state."""
        return list(self._queue)

    def add(self, *actions: Tuple[Action, ...]):
        """Adds one or more actions to the queue."""
        for action in actions:
            if not isinstance(action, Action):
                raise TypeError(f"Expected Action, got {action!r}")
            self._queue.add(action)

    def process_all(self, game: Game):
        """Processes all actions, according to the given game state."""

        while len(self._queue) > 0:
            self.process_next(game=game)

    def process_next(self, game: Game):
        """Processes the next action, according to the given game state."""

        next_actions = self._get_next_actions(game)

        # Get and run all pre-action responses
        pre_responses = []
        for action in next_actions:
            pre_responses += game.broadcast_event(EPreAction(action))
        pre_queue = ActionQueue(queue=pre_responses, depth=self._depth + 1)
        pre_queue.process_all(game=game)
        self._history += pre_queue._history

        # Run the actions themselves
        for action in next_actions:
            if not action.canceled:
                action.doit(game)
                self._history.append(action)

        # Get and run all post-action responses
        post_responses = []
        for action in next_actions:
            post_responses += game.broadcast_event(EPostAction(action))
        post_queue = ActionQueue(queue=post_responses, depth=self._depth + 1)
        post_queue.process_all(game=game)
        self._history += post_queue._history

    def _get_next_actions(self, game: Game) -> List[Action]:
        """Gets the next 'batch' of actions to execute (with the same priority)."""

        if len(self._queue) == 0:
            return []

        res = []
        priority = self._queue[0].priority
        while (len(self._queue) > 0) and (self._queue[0].priority == priority):
            action: Action = self._queue.pop(0)
            res.append(action)
        return res

    def __repr__(self) -> str:
        cn = type(self).__qualname__
        return f"<{cn} with {len(self._queue)} queued, {len(self._history)} in history>"


class Game(_EventEngine):
    """Holds game state and logic.

    Attributes
    ----------
    current_phase : Phase
        Defines the current phase, including how actions are resolved.
    alignments : List[Alignment]
    actors : List[Actor]
    subscribers : Dict[str, List[Subscriber]]
        Map between event types (as str hierarchies) and Subscribers.
    """

    def __init__(
        self,
        *,
        alignments: List[Alignment] = None,
        actors: List[Actor] = None,
        phases: PhaseCycle = None,
        subscribers: Dict[str, List[Subscriber]] = None,
        action_queue: ActionQueue = None,
    ):
        super().__init__(subscribers=subscribers)

        if phases is None:
            phases = PhaseCycle.make_day_night()
        if alignments is None:
            alignments: List[Alignment] = []
        if actors is None:
            actors: List[Actor] = []
        if action_queue is None:
            action_queue = ActionQueue()

        # Read-only properties
        self._phases = phases
        self._action_queue = action_queue
        self._alignments = alignments
        self._actors = actors

    def __repr__(self) -> str:
        cn = type(self).__qualname__
        return f"{cn}(...)"

    @property
    def action_queue(self) -> ActionQueue:
        return self._action_queue

    @property
    def phases(self) -> PhaseCycle:
        return self._phases

    @property
    def current_phase(self) -> Phase:
        return self._phases.current

    @property
    def actors(self) -> List[Actor]:
        return list(self._actors)

    @property
    def alignments(self) -> List[Alignment]:
        return list(self._alignments)

    def process_event(self, event: Event, *, process_now: bool = False) -> None:
        """Broadcasts event and processes all responses."""

        # ActionResolutionType.instant processes everything on phase change
        # ActionResolutionType.end_of_phase should only process all on phase change

        process_now = (
            process_now
            or isinstance(event, EPhaseEnd)
            or (self.current_phase.action_resolution == ActionResolutionType.instant)
        )

        actions = self.broadcast_event(event)
        self.action_queue.add(*actions)

        if process_now:
            self.action_queue.process_all(self)
