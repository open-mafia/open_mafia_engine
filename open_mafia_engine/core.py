from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
import logging
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from sortedcontainers import SortedList

from open_mafia_engine.util.repr import ReprMixin


logger = logging.getLogger(__name__)


class GameObject(ReprMixin):
    """Core game object."""


class Event(GameObject):
    """Represents some event."""

    @classmethod
    def default_code(cls) -> str:
        """Gets the hierarchy code for this event type."""
        mro = cls.mro()
        parts = []
        for cls in mro:
            parts.append(cls.__qualname__)
            if cls is Event:
                break
        return ":".join(reversed(parts))

    def code(self) -> str:
        """Gets the code for this particular event."""
        return self.default_code()


class Action(ABC, GameObject):
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


class Subscriber(ABC):
    """Mixin class for objects that need to recieve event broadcasts."""

    @abstractmethod
    def respond_to_event(self, event: Event, game: Game) -> Optional[Action]:
        """Respond to an event, given the game context."""
        return None

    @abstractmethod
    def subscribe(self, game: Game) -> None:
        """Subscribe to some particular event type(s)."""

    @abstractmethod
    def unsubscribe(self, game: Game) -> None:
        """Unsubscribe from some particular event type(s)."""


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

    def add(self, action: Action):
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


class Alignment(GameObject):
    """A 'team' of Actors.

    Attributes
    ----------
    name : str
    actors : List[Actor]

    TODO: Add wincons.
    """

    def __init__(self, name: str, actors: List[Actor] = None):
        if actors is None:
            actors = []
        self.name = name
        self._actors = list(actors)

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


class Actor(GameObject):
    """Represents a person or character.

    Attributes
    ----------
    name : str
    alignments : List[Alignment]
    abilities : List[Ability]
    """

    def __init__(
        self,
        name: str,
        alignments: List[Alignment] = None,
        abilities: List[Ability] = None,
    ):
        if abilities is None:
            abilities = []
        if alignments is None:
            alignments = []
        self.name = name

        # "parent" alignment
        self._alignments = list(alignments)
        for al in self._alignments:
            al.add_actor(self)

        self._abilities = list(abilities)

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
        if al not in self._alignments:
            self._alignments.append(al)
            al.add_actor(self)

    def remove_alignment(self, al: Alignment):
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


class Ability(GameObject):
    """An Ability is a part of the role that allows some sort of action.

    Attributes
    ----------
    name : str
    owner : Actor
        Abilities must always have an owner that points back at them.
    constraints : List[Constraint]
        Constraints on ability usage.
    """

    def __init__(self, name: str, owner: Actor, constraints: List[Constraint] = None):
        if constraints is None:
            constraints = []
        self.name = name

        self._owner = owner
        self._owner._abilities.append(self)

        self._constraints = list(constraints)
        for c in constraints:
            self.take_control_of_constraint(c)

    def clone(self, new_owner: Actor) -> Ability:
        """Clones this ability with a new owner."""
        raise NotImplementedError("TODO: Implement")

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
    """Event of intent to activate an ability."""

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
        return cls.default_code() + ":" + type(atype).__qualname__


class ActivatedAbility(Ability, Subscriber):
    """Ability that is activated by the `EActivateAbility` event.

    Override `make_action` for your custom abilities.
    """

    def __init__(self, name: str, owner: Actor, constraints: List[Constraint] = None):
        super().__init__(name, owner, constraints=constraints)

    @abstractmethod
    def make_action(self, game: Game, **params) -> Optional[Action]:
        raise NotImplementedError(f"No `make_action` for {self!r}")

    def subscribe(self, game: Game) -> None:
        game.add_sub(self, EActivateAbility.code_for(type(self)))

    def unsubscribe(self, game: Game) -> None:
        game.remove_sub(self, EActivateAbility.code_for(type(self)))

    def respond_to_event(self, event: Event, game: Game) -> Optional[Action]:
        if isinstance(event, EActivateAbility):
            if event.ability is self:
                return self.make_action(game=game, **event.params)
        return None


class Constraint(GameObject):
    def __init__(self, parent: Ability):
        self._parent = parent
        self._parent._constraints.append(self)

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


class Game(ReprMixin):
    """Holds game state and logic.

    Attributes
    ----------
    current_phase : Phase
        Defines the current phase, including how actions are resolved.
    game_actor : Actor
        The fake actor that represents the game's actions.
        By default, this is an empty actor (e.g. no automation).
    alignments : List[Alignment]
    actors : List[Actor]
    subscribers : Dict[str, List[Subscriber]]
        Map between event types (as str hierarchies) and Subscribers.
    """

    def __init__(
        self,
        *,
        current_phase: Phase,
        game_actor: Actor = None,
        alignments: List[Alignment] = None,
        actors: List[Actor] = None,
        subscribers: Dict[str, List[Subscriber]] = None,
    ):
        if alignments is None:
            alignments: List[Alignment] = []
        if actors is None:
            actors: List[Actor] = []
        if subscribers is None:
            subscribers = {}
        if game_actor is None:
            game_actor = Actor(name="game")
        # TODO: Maybe hide behind properties?
        # Probably only if we add backlinks.
        self.game_actor = game_actor
        self.current_phase = current_phase
        self.alignments = alignments
        self.actors = actors
        self._subscribers = defaultdict(list, subscribers)

    @property
    def subscribers(self) -> Dict[str, List[Subscriber]]:
        return dict(self._subscribers)

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

        affected_subs = []
        for i in range(len(parts) + 1):  # including "" and `event.code()`
            subs_i = self._subscribers[":".join(parts[:i])]
            affected_subs += [s for s in subs_i if s not in affected_subs]

        res = []
        for sub in affected_subs:
            response = sub.respond_to_event(event=event, game=self)
            if response is not None:
                res.append(response)
        return res
