from __future__ import annotations

import inspect
import logging
import warnings
from abc import abstractmethod
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    List,
    MutableMapping,
    Optional,
    Tuple,
    Type,
    Union,
)

from makefun import with_signature

from open_mafia_engine.core.event_system import Action, Event, Subscriber, handler
from open_mafia_engine.core.game_object import GameObject, inject_converters
from open_mafia_engine.core.naming import get_path

# from open_mafia_engine.core.outcome import Outcome, OutcomeAction

if TYPE_CHECKING:
    from open_mafia_engine.core.game import Game

logger = logging.getLogger(__name__)


class Faction(GameObject):
    """Faction, a.k.a. Alignment."""

    def __init__(self, game: Game, /, name: str):
        self.name = name
        self._actors: List[Actor] = []
        self._outcome_checkers: List[OutcomeChecker] = []
        super().__init__(game)

    @property
    def actors(self) -> List[Actor]:
        return list(self._actors)

    @property
    def actor_names(self) -> List[str]:
        return [x.name for x in self._actors]

    @property
    def outcome_checkers(self) -> List[OutcomeChecker]:
        return list(self._outcome_checkers)

    @inject_converters
    def add_actor(self, actor: Actor):
        if not isinstance(actor, Actor):
            raise TypeError(f"Expected Actor, got {actor!r}")
        if actor in self._actors:
            return
        self._actors.append(actor)
        actor._factions.append(self)

    @inject_converters
    def remove_actor(self, actor: Actor):
        if actor in self._actors:
            self._actors.remove(actor)
        if self in actor._factions:
            actor._factions.remove(self)

    def add_outcome_checker(self, oc: OutcomeChecker):
        if not isinstance(oc, OutcomeChecker):
            raise TypeError(f"Expected OutcomeChecker, got {oc!r}")
        if oc in self._outcome_checkers:
            return
        self._outcome_checkers.append(oc)
        oc.parent = self

    # def remove_outcome_checker(self, oc: OutcomeChecker):
    #     if oc in self._outcome_checkers:
    #         self._outcome_checkers.remove(self)
    #         # Wait, what do we do with `oc._parent`?!


class OutcomeChecker(Subscriber):
    """Checks for Faction Outcome. Base class."""

    def __init__(self, game: Game, parent: Faction, /):
        super().__init__(game)
        self._parent = parent
        parent.add_outcome_checker(self)

    @property
    def parent(self) -> Faction:
        return self._parent


class Actor(GameObject):
    """Actor object."""

    def __init__(self, game: Game, /, name: str, status: Dict[str, Any] = None):
        if status is None:
            status = {}
        self.name = name
        self._abilities: List[Ability] = []
        self._triggers: List[Trigger] = []
        self._factions: List[Faction] = []
        self._status: Status = Status(game, self, **status)
        super().__init__(game)

    @property
    def status(self) -> Status:
        return self._status

    @property
    def abilities(self) -> List[Ability]:
        return list(self._abilities)

    @property
    def ability_names(self) -> List[str]:
        return [a.name for a in self._abilities]

    @property
    def triggers(self) -> List[Trigger]:
        return list(self._triggers)

    @property
    def trigger_names(self) -> List[str]:
        return [t.name for t in self._triggers]

    @property
    def factions(self) -> List[Faction]:
        return list(self._factions)

    def add_ability(self, ability: Ability):
        """Adds this ability to self, possibly removing the old owner."""
        if not isinstance(ability, Ability):
            raise TypeError(f"Expected Ability, got {ability!r}")
        if ability in self._abilities:
            return
        self._abilities.append(ability)
        if ability._owner is not self:
            ability._owner._abilities.remove(ability)
            ability._owner = self

    def add_trigger(self, trigger: Trigger):
        """Adds this trigger to self, possibly removing the old owner."""
        if not isinstance(trigger, Trigger):
            raise TypeError(f"Expected Trigger, got {trigger!r}")
        if trigger in self._triggers:
            return
        self._triggers.append(trigger)
        if trigger._owner is not self:
            trigger._owner._triggers.remove(trigger)
            trigger._owner = self

    def add(self, obj: Union[Ability, Trigger, Faction]):
        """Adds """
        if isinstance(obj, Ability):
            self.add_ability(obj)
        elif isinstance(obj, Trigger):
            self.add_trigger(obj)
        elif isinstance(obj, Faction):
            warnings.warn("Better to do `Faction.add_actor(me)` directly.")
            obj.add_actor(self)
        else:
            raise TypeError(f"Expected Ability or Trigger, got {obj!r}")


class _ATBase(Subscriber):
    """Base object for abilities and triggers.

    Attributes
    ----------
    game
    owner : Actor
    name : str
        The Ability's name.
    desc : str
        Description. Default is "".
    """

    def __init__(self, game: Game, /, owner: Actor, name: str, desc: str = ""):
        if not isinstance(owner, Actor):
            raise TypeError(f"Expected Actor, got {owner!r}")
        if desc is None:
            desc = ""

        self._owner = owner
        self._name = str(name)
        self._desc = str(desc)
        super().__init__(game)
        owner.add(self)
        owner.add_ability(self)

    @property
    def owner(self) -> Actor:
        return self._owner

    @property
    def name(self) -> str:
        return self._name

    @property
    def desc(self) -> str:
        return self._desc


class Trigger(_ATBase):
    """Basic Trigger object.

    Attributes
    ----------
    game
    owner : Actor
    name : str
        The Trigger's name.
    desc : str
        Description. Default is "".
    """

    @property
    def path(self) -> str:
        return get_path(self.owner.name, "trigger", self.name)


class EActivate(Event):
    """Event of ability activation.

    That is, this event is triggered by a player trying to activate their Ability.
    """

    def __init__(self, game, ability: Ability, /, *args, **kwargs):
        self._ability = ability
        self._args = args
        self._kwargs = kwargs
        super().__init__(game)

    @property
    def ability(self) -> Ability:
        return self._ability

    @property
    def args(self) -> Tuple:
        return self._args

    @property
    def kwargs(self) -> Dict[str, Any]:
        return dict(self._kwargs)


class Ability(_ATBase):
    """Basic Ability object.

    Attributes
    ----------
    game
    owner : Actor
    name : str
        The Ability's name.
    desc : str
        Description. Default is "".
    """

    @property
    def path(self) -> str:
        return get_path(self.owner.name, "ability", self.name)

    @abstractmethod
    def activate(self, *args, **kwargs) -> Optional[List[Action]]:
        """Activate this ability with some arguments."""

        # TODO: Implement argument constraints!
        # TODO: Make the signature be the same as the Action's

    @handler
    def handle_activate(self, event: EActivate) -> Optional[List[Action]]:
        """Handler to activate this ability."""
        if isinstance(event, EActivate) and event.ability is self:
            return self.activate(*event.args, **event.kwargs)
        return None

    @classmethod
    def generate(
        cls,
        action_or_func: Union[Type[Action], Callable],
        params: List[str] = None,
        name: str = None,
        doc: str = None,
        desc: str = None,
    ) -> Type[Ability]:
        """Create an Ability subtype from an Action or function.

        Parameters
        ----------
        action_or_func : Type[Action] or Callable
            If an Action subclass, uses it directly.
            If a callable (function), generates an action type and uses it.
        params : List[str]
            The names of parameters to leave as activation parameters.
            The rest will be taken as arguments for the Ability itself.
        """

        # Create an action type
        if isinstance(action_or_func, type) and issubclass(action_or_func, Action):
            TAction = action_or_func
        elif callable(action_or_func):
            gen_name: str = name if name else f"{action_or_func.__name__}_Action"
            TAction = Action.generate(action_or_func, name=gen_name, doc=doc)
        else:
            raise TypeError(f"Expected Action or function, got {action_or_func!r}")
        TAction: Type[Action]

        # Fix input arguments
        if params is None:
            params = []
        if name is None:
            name = f"{cls.__name__}_{TAction.__name__}"
            # TODO - add random bits to avoid conflict?
        if doc is None:
            doc = "(GENERATED ABILITY) " + (TAction.__doc__ or "")

        # Split the signature into __init__() and activate() args
        sig_action = inspect.signature(TAction.__init__)
        par_action = list(sig_action.parameters.values())

        par_activate = [
            inspect.Parameter("self", kind=inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ] + [p for p in par_action if p.name in params]
        sig_activate = inspect.Signature(
            par_activate, return_annotation=Optional[List[Action]]
        )

        sig_init = "TODO"

        # TODO: Set sig_init
        def __init__(self, game: Game, /, owner: Actor, name: str, desc: str = ""):
            super().__init__(game, owner, name, desc=desc)

        @with_signature(sig_activate)
        def activate(self, *args, **kwargs) -> Optional[List[Action]]:
            """Activate this ability with some arguments."""

            try:
                return [self.TAction(self.game, *args, **kwargs)]
            except Exception as e:
                logger.exception("Error executing action:")
                if False:  # Set for debugging errors :)
                    raise
                return None

        GeneratedAbility = type(
            name, (cls,), {"__init__": __init__, "activate": activate, "__doc__": doc}
        )
        GeneratedAbility.TAction = TAction

        return GeneratedAbility


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

    def __init__(self, game, /, parent: Actor, **attribs: Dict[str, Any]):
        super().__init__(game)
        self._parent = parent
        self._attribs = attribs

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
        self.game.process_event(
            EStatusChange(self.game, self.parent, key, old_val, None)
        )

    def __setitem__(self, key, value) -> None:
        old_val = self[key]
        self._attribs[key] = value
        if old_val == value:  # TODO: Maybe broadcast always?
            return
        self.game.process_event(
            EStatusChange(self.game, self.parent, key, old_val, value)
        )

    def __len__(self) -> int:
        return len(self._attribs)

    def __iter__(self):
        return iter(self._attribs)

    def __repr__(self):
        cn = type(self).__qualname__
        parts = [repr(self.game), repr(self.parent)]
        for k, v in self._attribs.items():
            parts.append(f"{k}={v!r}")
        return f"{cn}(" + ", ".join(parts) + ")"


class EStatusChange(Event):
    """The Status has changed for some Actor."""

    def __init__(self, game, /, actor: Actor, key: str, old_val: Any, new_val: Any):
        super().__init__(game)
        self._actor = actor
        self._key = key
        self._old_val = old_val
        self._new_val = new_val

    @property
    def actor(self) -> Actor:
        return self._actor

    @property
    def status(self) -> Status:
        return self._actor.status

    @property
    def key(self) -> str:
        return self._key

    @property
    def old_val(self) -> Any:
        return self._old_val

    @property
    def new_val(self) -> Any:
        return self._new_val
