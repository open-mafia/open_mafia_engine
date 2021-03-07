from __future__ import annotations
from collections import defaultdict
from typing import List, Dict, Type, Union
from pydantic import BaseModel, parse_obj_as


class HookModel(BaseModel):
    """Base model to add "hooks", which parse the model as derivative classes.

    To subclass, define the Hook internal class (type annotations are optional):

        class Hook:
            subtypes: Dict[str, Type[YourType]] = {}
            builtins: Dict[str, YourType] = {}
            defaults: Dict[str, YourType] = {}
    """

    type: str

    # Override this internal class with your own!
    class Hook:
        subtypes: Dict[str, Type[HookModel]]
        builtins: Dict[str, HookModel]
        defaults: Dict[str, HookModel]

    def __init_subclass__(cls, default: bool = False):
        """This handles dispatching on hook `type`, if given."""

        fld_t = cls.__fields__["type"]
        ctype = fld_t.default

        if ctype is None:
            # ignore if there is no `type` specified; likely "abstract"
            return

        if ctype in cls.Hook.subtypes:
            et = cls.Hook.subtypes[ctype]
            raise ValueError(f"Subtype {ctype!r} exists for {et!r}")
        cls.Hook.subtypes[ctype] = cls
        if default:
            cls.Hook.defaults[cls.__qualname__] = cls()

    @classmethod
    def parse_single(cls, c: Union[str, HookModel, dict]) -> HookModel:
        """This parses the passed dict (or str builtin) as a HookModel."""

        # If already a HookModel, don't touch it.
        if isinstance(c, HookModel):
            # TODO: Maybe check that the `type` matches the class default?
            return c  # TODO: Maybe also return a copy?

        # If a string, check builtins
        if isinstance(c, str):
            x = cls.Hook.builtins.get(c)
            if x is None:
                raise ValueError(f"Could not find built-in hook named {c!r}")
            return x.copy()  # make sure to return a copy :)

        # Must be dict-like
        # Find the class for this type
        ts = c.get("type")
        if ts is None:
            raise ValueError("No 'type' specified.")
        T = cls.Hook.subtypes.get(ts)
        if T is None:
            raise ValueError(f"No HookModel found for type={ts!r}")
        # Let Pydantic handle parsing this object
        return parse_obj_as(T, c)

    @classmethod
    def parse_list(cls, cs: List[Union[str, HookModel, dict]]) -> List[HookModel]:
        """Parses a list of constraints, adding defaults if not set explicitly."""

        global __constraint_defaults__

        res: List[HookModel] = []

        # Checks if default was overridden (via class)
        ovrd_defaults: Dict[str, HookModel] = defaultdict(lambda: False)

        for c in cs:
            x = cls.parse_single(c)
            xnm = type(x).__qualname__
            if xnm in cls.Hook.defaults:
                ovrd_defaults[xnm] = True
            res.append(x)

        # Add (copies of) defaults that weren't overridden
        for k, v in cls.Hook.defaults.items():
            if not ovrd_defaults[k]:
                res.append(v.copy())
        return res

    @classmethod
    def update_builtins(cls, d: Dict[str, dict]) -> None:
        """Updates the built-in hooks from the mapping (doesn't overwrite keys)."""

        if d is None:
            return

        for k, v in d.items():
            old = cls.Hook.builtins.get(k)
            if old is not None:
                raise ValueError(f"Builtin named {k!r} already exists: {old!r}")
            cls.Hook.builtins[k] = cls.parse_single(v)
