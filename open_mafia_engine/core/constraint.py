from __future__ import annotations
from abc import abstractmethod
from collections import defaultdict
from typing import List, Dict, Optional, Type, Union
from pydantic import BaseModel, validator, parse_obj_as


__constraint_types__: Dict[str, Type[Constraint]] = {}
__constraint_builtins__: Dict[str, Constraint] = {}
__constraint_defaults__: Dict[str, Constraint] = {}


class Constraint(BaseModel):
    """Base constraint data type.

    To create a constraint, subclass this, change the 'type' default value,
    and make sure it's imported.
    """

    type: str

    def __init_subclass__(cls, default: bool = False):
        """This handles dispatching on constraint `type`, if given."""

        fld_t = cls.__fields__["type"]
        ctype = fld_t.default
        if ctype is None:
            return
        if ctype in __constraint_types__:
            et = __constraint_types__[ctype]
            raise ValueError(f"Constraint {ctype!r} exists for {et!r}")
        __constraint_types__[ctype] = cls
        if default:
            __constraint_defaults__[cls.__qualname__] = cls()

    @classmethod
    def parse_single(cls, c: Union[str, Constraint, dict]) -> Constraint:
        """This parses the passed dict (or str builtin) as a Constraint."""

        global __constraint_types__
        global __constraint_builtins__

        # If already a Constraint, don't touch it.
        if isinstance(c, Constraint):
            # TODO: Maybe check that the `type` matches the class default?
            return c  # TODO: Maybe also return a copy?

        # If a string, check builtins
        if isinstance(c, str):
            x = __constraint_builtins__.get(c)
            if x is None:
                raise ValueError(f"Could not find built-in constraint named {c!r}")
            return x.copy()  # make sure to return a copy :)

        # Must be dict-like
        # Find the class for this type
        ts = c.get("type")
        if ts is None:
            raise ValueError("No 'type' specified.")
        T = __constraint_types__.get(ts)
        if T is None:
            raise ValueError(f"No Constraint found for type={ts!r}")
        # Let Pydantic handle parsing this object
        return parse_obj_as(T, c)

    @classmethod
    def parse_list(cls, cs: List[Union[str, Constraint, dict]]) -> List[Constraint]:
        """Parses a list of constraints, adding defaults if not set explicitly."""

        global __constraint_defaults__

        res: List[Constraint] = []

        # Checks if default was overridden (via class)
        ovrd_defaults: Dict[str, Constraint] = defaultdict(lambda: False)

        for c in cs:
            x = cls.parse_single(c)
            xnm = type(x).__qualname__
            if xnm in __constraint_defaults__:
                ovrd_defaults[xnm] = True
            res.append(x)

        # Add (copies of) defaults that weren't overridden
        for k, v in __constraint_defaults__.items():
            if not ovrd_defaults[k]:
                res.append(v.copy())
        return res

    @classmethod
    def update_builtins(cls, d: Dict[str, dict]) -> None:
        """Updates the built-in constraints from the mapping (can't overwrite keys)."""

        global __constraint_builtins__

        for k, v in d.items():
            old = __constraint_builtins__.get(k)
            if old is not None:
                raise ValueError(f"Builtin named {k!r} already exists: {old!r}")
            __constraint_builtins__[k] = cls.parse_single(v)


class AliveConstraint(Constraint, default=True):
    """Actor must be alive. Default is 'true'. """

    type: str = "alive"
    value: Optional[bool] = True


class ActionLimitPerPhaseConstraint(Constraint, default=True):
    """Limits the numbers of actions taken per phase. Default is 1."""

    type: str = "action_limit"
    n_actions: Optional[int] = 1


class PhaseConstraint(Constraint):
    """Ability may be used only during this phase."""

    type: str = "phase"
    phases: List[str]


class KeyPhaseConstraint(PhaseConstraint):
    """All abilities with the `key` can only be used N times per phase.

    Most notably, this is useful for faction-wide kills/abilities.

    Attributes
    ----------
    type : "key_phase_limited"
    key : str
        The key to constrain to. This can be arbitrary, e.g. "faction-mafia"
    phases : List
        The phases to use. These must be a subset of the defined phases.
    uses : int
        The number of faction uses per each phase.
    """

    type: str = "key_phase_limited"
    key: str
    phases: List[str]
    uses: int = 1


class NShotConstraint(Constraint):
    """Ability may only be used N times total during the game."""

    type: str = "n_shot"
    uses: int
