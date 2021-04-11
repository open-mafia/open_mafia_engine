from __future__ import annotations

from enum import Enum
from typing import Dict, Type, Union

from pydantic import parse_obj_as

from open_mafia_engine.util.hook import HookModel


class ActionResolution(str, Enum):
    """When actions are resolved."""

    instant = "instant"
    end_of_phase = "end_of_phase"


class Phase(HookModel):
    """Phase definition.

    Attributes
    ----------
    name : str
    desc : str = "<no description>"
    action_resolution : ActionResolution

    Note
    ----
    This class overrides the HookType `parse_single` definition to not require
    the "type" to be specified.
    """

    type: str = "phase"
    name: str
    desc: str = "<no description>"
    action_resolution: ActionResolution

    class Hook:
        subtypes: Dict[str, Type[Phase]] = {}
        builtins: Dict[str, Phase] = {}
        defaults: Dict[str, Phase] = {}

    @classmethod
    def parse_single(cls, c: Union[str, Phase, dict]) -> Phase:
        """This parses the passed dict (or str builtin) as a Phase."""

        # If already a Phase, don't touch it.
        if isinstance(c, Phase):
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
            T = Phase
        else:
            T = cls.Hook.subtypes.get(ts)
        if T is None:
            raise ValueError(f"No Phase found for type={ts!r}")
        # Let Pydantic handle parsing this object
        return parse_obj_as(T, c)


Phase.Hook.subtypes["phase"] = Phase
