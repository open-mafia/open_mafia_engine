from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
import logging
from typing import DefaultDict, Dict, List, Optional, Type, Union
from uuid import UUID, uuid4

from open_mafia_engine.util.repr import ReprMixin


logger = logging.getLogger(__name__)

__object_types__ = {}


class GameObject(ReprMixin):
    """Base class for game objects."""

    def __init_subclass__(cls, name: str = None) -> None:
        global __object_types__
        if name is None:
            name = cls.__qualname__
        __object_types__[name] = cls


class Event(ABC, GameObject):
    """Core event object."""

    @classmethod
    def _default_parts(cls) -> List[str]:
        """Gets the backwards MRO, starting from Event."""
        mro = cls.mro()
        parts = []
        for cls in mro:
            parts.append(cls.__qualname__)
            if cls is Event:
                break
        parts = list(reversed(parts))
        return parts

    # @abstractmethod
    def _code_parts(self) -> List[str]:
        """Internal definition of code parts. Override this.

        Example implementation (correctly includes own type):

            def _code_parts(self) -> List[str]:
                parts = super()._code_parts()
                return parts + [str(self.blah)]
        """
        return type(self)._default_parts()

    @property
    def code(self) -> str:
        """Returns the event code, as a string."""
        _parts = self._code_parts()
        assert all(":" not in x for x in _parts)
        return ":".join(_parts)


EType = Type[Event]
EventTLike = Union[EType, str]


class Action(ABC, GameObject):
    """Base action class. Override __init__() and __call__().

    Attributes
    ----------
    source_id : UUID
        The direct source of the action, e.g. an Ability, rather than Actor.
    priority : float
        The action priority for the queue. Default is 0.
    canceled : bool
        Whether the action was canceled (as a result of other actions).
    """

    def __init__(self, source_id: UUID, *, priority: float = 0, canceled: bool = False):
        self.source_id = source_id
        self.priority = float(priority)
        self.canceled = bool(canceled)

    def __lt__(self, other: Action):
        if not isinstance(other, Action):
            return NotImplemented
        return self.priority > other.priority  # We sort decreasing by priority!

    @abstractmethod
    def __call__(self) -> None:
        """This actually executes the action."""


class PreActionE(Event):
    """Event that happens before an action."""

    def __init__(self, action_id: UUID):
        self.action_id = action_id

    def _code_parts(self) -> List[str]:
        parts = super()._code_parts()
        return parts + [str(self.action_id)]


class PostActionE(Event):
    """Event that happens after an action."""

    def __init__(self, action_id: UUID):
        self.action_id = action_id

    def _code_parts(self) -> List[str]:
        parts = super()._code_parts()
        return parts + [str(self.action_id)]


class Subscriber(ABC):
    """Mixin type for subscriber objects."""

    @abstractmethod
    def respond(self, event: Event) -> Optional[Action]:
        """Respond to an Event."""
        return None

    def sub(self, *events: List[EventTLike]) -> None:
        """Subscribes to one or more events."""
        GameEngine.current().add_sub(self, *events)

    def unsub(self, *events: List[EventTLike]) -> None:
        """Unsubscribes from one or more events."""
        GameEngine.current().remove_sub(self, *events)


__active_engines__ = []


class GameEngine(object):
    """Game engine.

    Attributes
    ----------
    state : Dict[UUID, GameObject]
        Mapping of object IDs to their objects.
    subscribers : DefaultDict[str, List[GameObject]]
        Mapping of event types to their subscribers.
    """

    def __init__(
        self,
        state: Dict[UUID, GameObject] = None,
        subscribers: DefaultDict[str, List[GameObject]] = None,
    ):
        if state is None:
            state = {}
        self.state: Dict[str, GameObject] = state
        if subscribers is None:
            subscribers = defaultdict(list)
        self.subscribers = subscribers

    @classmethod
    def current(cls) -> GameEngine:
        if len(__active_engines__) == 0:
            raise ValueError("No engine is currently active, even default.")
        return __active_engines__[-1]

    def add_object(self, obj: GameObject, id: UUID = None) -> UUID:
        """Adds the object. If there is no ID passed, creates a new ID."""
        if id is None:
            id = uuid4()
        elif isinstance(id, UUID):
            pass
        elif isinstance(id, str):
            id = UUID(id)
        else:
            raise ValueError(f"Expected UUID, got {id!r}")
        if not isinstance(obj, GameObject):
            raise TypeError(f"Expected GameObject, got {obj!r}")
        self.state[id] = obj
        return id

    def get_responses(self, event: Event) -> List[Action]:
        """Gets responses from all subscribers."""

        # NOTE: We need to de-duplicate subscribers, since you can sub to "X" and "X:Y"
        subs: List[Subscriber] = []
        parts = event.code.split(":")
        for i in range(len(parts) + 1):
            eparts = ":".join(parts[:i])
            subs += [s for s in self.subscribers[eparts] if s not in subs]

        actions: List[Action] = []
        for sub in subs:
            x = sub.respond(event)
            if x is not None:
                actions.append(x)
        return actions

    def add_sub(self, sub: Subscriber, *etypes: List[EventTLike]):
        """Adds subscriptions to `sub`."""
        for etype in etypes:
            if isinstance(etype, str):
                event_str = etype
            elif issubclass(etype, Event):
                event_str = ":".join(etype._default_parts())
            # if sub not in self.subscribers[event_str]:
            self.subscribers[event_str].append(sub)

    def remove_sub(self, sub: Subscriber, *etypes: List[EventTLike]):
        """Removes subscriptions from `sub`."""
        for etype in etypes:
            if isinstance(etype, str):
                event_str = etype
            elif issubclass(etype, Event):
                event_str = ":".join(etype._default_parts())

            try:
                self.subscribers[event_str].remove(sub)
            except ValueError:
                logger.exception(f"Attempted to unsubscribe {sub} from {etype}.")

    def __repr__(self) -> str:
        cn = type(self).__qualname__
        n_obj = len(self.state)
        s = "" if n_obj == 1 else "s"
        return f"<{cn} with {n_obj} object{s}>"

    def __enter__(self) -> GameEngine:
        global __active_engines__
        __active_engines__.append(self)
        return self

    def __exit__(self, exc_type=None, exc_value=None, tb=None) -> Optional[bool]:
        if (len(__active_engines__) == 0) or (__active_engines__[-1] is not self):
            raise ValueError("Engine stack is corrupted!")
        __active_engines__.pop()
        return super().__exit__(exc_type, exc_value, tb)

    def __getitem__(self, id: UUID) -> GameObject:
        """Gets the object of the given ID by state."""
        if isinstance(id, UUID):
            pass
        elif isinstance(id, str):
            id = UUID(id)
        else:
            raise TypeError(f"Keys must be UUID, got {id!r}")
        return self.state[id]

    def __setitem__(self, id: UUID, obj: GameObject):
        self.add_object(obj=obj, id=id)


default_engine = GameEngine().__enter__()


class Alignment(GameObject):
    """A "team" for players.

    TODO: Wincon?
    """

    def __init__(self, name: str):
        self.name = name


class Actor(GameObject):
    """An active participant of the game.

    Attributes
    ----------
    name : str
        The actor's name (human-readable).
    alignment_id : UUID
        The parent alignment.
    ability_ids : List[UUID]
        The abilities this Actor has.
    """

    def __init__(self, name: str, alignment_id: UUID, ability_ids: List[UUID]):
        self.name = name
        self.alignment_id = alignment_id
        self.ability_ids = ability_ids

    @property
    def alignment(self) -> Alignment:
        al = GameEngine.current()[self.alignment_id]
        if not isinstance(al, Alignment):
            raise TypeError(f"Object is not an Alignment: {al}")
        return al

    @property
    def abilities(self) -> List[Ability]:
        e = GameEngine.current()
        res = []
        for id in self.ability_ids:
            x = e[id]
            if not isinstance(x, Ability):
                raise TypeError(f"Object is not an Ability: {x}")
        return res


class Ability(GameObject):
    """An ability.

    Attributes
    ----------
    name : str
        The ability name (human-readable).
    actor_id : UUID
        The parent actor.
    constraint_ids : List[UUID]
        The constraints that apply to this ability.
    """

    def __init__(self, name: str, actor_id: UUID, constraint_ids: List[UUID]):
        self.name = name
        self.actor_id = actor_id
        self.constraint_ids = constraint_ids

    @property
    def actor(self) -> Actor:
        act = GameEngine.current()[self.actor_id]
        if not isinstance(act, Actor):
            raise TypeError(f"Object is not an Actor: {act}")
        return act

    @property
    def constraints(self) -> List[Constraint]:
        e = GameEngine.current()
        res = []
        for id in self.constraint_ids:
            x = e[id]
            if not isinstance(x, Constraint):
                raise TypeError(f"Object is not a Constraint: {x}")
        return res


class Constraint(GameObject):
    """A constraint on the (possibly automatic) usage of an ability.

    Attributes
    ----------
    ability_id : UUID
        The parent ability.
    """

    def __init__(self, ability_id: UUID):
        self.ability_id = ability_id

    @property
    def ability(self) -> Ability:
        """The parent Ability object."""
        abil = GameEngine.current()[self.ability_id]
        if not isinstance(abil, Ability):
            raise TypeError(f"Object is not an Ability: {abil}")
        return abil


class ActionResolutionType(str, Enum):
    """When actions are resolved."""

    instant = "instant"
    end_of_phase = "end_of_phase"


class Phase(GameObject):
    """This holds game phase information.

    Attributes
    ----------
    action_resolution : ActionResolutionType
        Determines how actions are resolved during this phase.
        One of: {"instant", "end_of_phase"}
    """

    def __init__(self, action_resolution: Union[ActionResolutionType, str]):
        self.action_resolution = ActionResolutionType(action_resolution)


class Vote(GameObject):
    """This is a basic vote.

    Attributes
    ----------
    source_id : UUID
        This is the source of the vote (e.g. voter).
    target_ids : List[UUID]
        Votes may have 0 or more targets.
    """

    def __init__(self, source_id: UUID, target_ids: List[UUID]):
        self.source_id = source_id
        self.target_ids = target_ids

    @property
    def source(self) -> GameObject:
        return GameEngine.current()[self.source_id]

    @property
    def targets(self) -> List[GameObject]:
        e = GameEngine.current()
        return [e[i] for i in self.target_ids]


class VoteTally(GameObject):
    """This holds voting information.

    Attributes
    ----------
    vote_ids : List[UUID]
        The votes that were cast.
    """

    def __init__(self, vote_ids: List[UUID]):
        self.vote_ids = vote_ids

    @property
    def votes(self) -> List[Vote]:
        e = GameEngine.current()
        res = []
        for id in self.vote_ids:
            x = e[id]
            if not isinstance(x, Vote):
                raise TypeError(f"Object is not a Vote: {x}")
        return res
