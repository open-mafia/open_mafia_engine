from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from enum import Enum
import logging
from typing import DefaultDict, Dict, List, Optional, Type, Union
from uuid import UUID, uuid4

from open_mafia_engine.util.repr import ReprMixin
from sortedcontainers.sortedlist import SortedKeyList, SortedList


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

    @property
    def source(self) -> GameObject:
        e = GameEngine.current()
        return e[self.source_id]

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


def _sorter_action_ids(id: UUID) -> float:
    return -GameEngine.current()[id].priority


class ActionContext(GameObject):
    """Context and queue."""

    def __init__(self, queued_ids: List[UUID] = None, history_ids: List[UUID] = None):
        if queued_ids is None:
            queued_ids = []
        if history_ids is None:
            history_ids = []

        self.queued_ids = SortedKeyList(queued_ids, key=_sorter_action_ids)
        self.history_ids = history_ids

    @property
    def history(self) -> List[Action]:
        e = GameEngine.current()
        return [e[id] for id in self.history_ids]

    @property
    def queue(self) -> List[Action]:
        e = GameEngine.current()
        return [e[id] for id in self.queued_ids]

    def enqueue(self, *action_ids: List[UUID]) -> None:
        """Enqueues one or more actions."""
        self.queued_ids.update(action_ids)

    def process_all(self):
        while len(self.queued_ids) > 0:
            self.process_next()

    def process_next(self):
        """Processes the next batch of Actions with the same priority."""

        engine = GameEngine.current()

        # Select all action IDs with the highest (equal) priority
        # ... and get pre-responses in parallel
        first_id = self.queued_ids[0]
        priority = engine[first_id].priority
        action_ids: List[Action] = []
        pre_responses: List[Action] = []
        while len(self.queued_ids) > 0:
            if engine[self.queued_ids[0]].priority != priority:
                break

            in_id: UUID = self.queued_ids.pop(0)
            e_pre = PreActionE(action_id=in_id)
            action_ids.append(in_id)
            pre_responses += engine.get_responses(e_pre)

        # Run pre-responses, which may change the actions
        pre_ids = [engine.add_object(resp) for resp in pre_responses]
        pre_context = ActionContext(queued_ids=pre_ids)
        pre_context.process_all()
        self.history_ids += pre_context.history_ids

        # Run all current actions, and get post-responses
        post_responses: List[Action] = []
        for action_id in action_ids:
            action: Action = engine[action_id]
            if not action.canceled:
                action()
                self.history_ids.append(action_id)

                e_post = PostActionE(action_id=action_id)
                post_responses += engine.get_responses(e_post)

        # Run post-responses, which can't change the actions
        post_ids = [engine.add_object(resp) for resp in post_responses]
        post_context = ActionContext(queued_ids=post_ids)
        post_context.process_all()
        self.history_ids += post_context.history_ids


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
        root_context: ActionContext = None,
    ):
        if state is None:
            state = {}
        self.state: Dict[str, GameObject] = state
        if subscribers is None:
            subscribers = defaultdict(list)
        self.subscribers = subscribers
        if root_context is None:
            root_context = ActionContext()
        self.root_context = root_context

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


class CancelAction(Action):
    """Action that cancels another action."""

    def __init__(
        self,
        source_id: UUID,
        target_id: UUID,
        *,
        priority: float = 100.0,
        canceled: bool = False,
    ):
        super().__init__(source_id, priority=priority, canceled=canceled)
        self.target_id = target_id

    def __call__(self) -> None:
        engine = GameEngine.current()
        target: Action = engine[self.target_id]
        target.canceled = True


class Constraint(GameObject, Subscriber):
    """A constraint on the (possibly automatic) usage of an ability.

    Attributes
    ----------
    ability_id : UUID
        The parent ability.
    """

    def __init__(self, ability_id: UUID):
        self.sub(PreActionE)
        self.ability_id = ability_id

    @abstractmethod
    def _check_if_allowed(self, action: Action) -> bool:
        return True

    def respond(self, event: Event) -> Optional[Action]:
        engine = GameEngine.current()
        if isinstance(event, PreActionE):
            a: Action = engine[event.action_id]
            if a.source_id == self.ability_id:
                if not self._check_if_allowed(a):
                    return CancelAction(
                        source_id=self.ability_id, target_id=event.action_id
                    )
        return None

    @property
    def ability(self) -> Ability:
        """The parent Ability object."""
        abil = GameEngine.current()[self.ability_id]
        if not isinstance(abil, Ability):
            raise TypeError(f"Object is not an Ability: {abil}")
        return abil


class PhaseConstraint(Constraint):
    """A constraint on the phase an ability is used."""

    def __init__(self, ability_id: UUID, phase_id: UUID):
        super().__init__(ability_id=ability_id)
        self.phase_id = phase_id

    def _check_if_allowed(self, action: Action) -> bool:
        engine = GameEngine.current()
        phase: Phase = engine[self.phase_id]
        # blah
        return True  # Blah


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

    def __init__(self, vote_ids: List[UUID] = []):
        self.vote_ids = list(vote_ids)

    @property
    def votes(self) -> List[Vote]:
        e = GameEngine.current()
        res = []
        for id in self.vote_ids:
            x = e[id]
            if not isinstance(x, Vote):
                raise TypeError(f"Object is not a Vote: {x}")
            res.append(x)
        return res


class VoteAction(Action):
    """Simple voting action."""

    def __init__(
        self,
        source_id: UUID,
        target_ids: List[UUID],
        tally_id: UUID,
        *,
        priority: float = 0.0,
        canceled: bool = False,
    ):
        super().__init__(source_id, priority=priority, canceled=canceled)
        self.target_ids = target_ids
        self.tally_id = tally_id

    def __call__(self) -> None:
        engine = GameEngine.current()
        tally: VoteTally = engine[self.tally_id]
        # add new votes (we don't care about old IDs, since the Tally behavior decides)
        new_vote = Vote(
            source_id=self.source_id, target_ids=[t for t in self.target_ids]
        )
        new_vote_id = engine.add_object(new_vote)
        tally.vote_ids.append(new_vote_id)
