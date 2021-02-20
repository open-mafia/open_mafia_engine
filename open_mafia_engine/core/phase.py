from __future__ import annotations
from enum import Enum
from typing import Dict
from pydantic import BaseModel

# from open_mafia_engine.util.hook import HookModel


class ActionResolution(str, Enum):
    """When actions are resolved."""

    instant = "instant"
    end_of_phase = "end_of_phase"


class Phase(BaseModel):
    """Phase definition.

    Attributes
    ----------
    name : str
    desc : str = "<no description>"
    action_resolution : ActionResolution

    Note
    ----
    This partially covers HookModel, but probably don't need to subclass phases.
    """

    name: str
    desc: str = "<no description>"
    action_resolution: ActionResolution

    class Hook:
        builtins: Dict[str, Phase] = {}

    @classmethod
    def update_builtins(cls, d: Dict[str, dict]) -> None:
        """Updates the built-in hooks from the mapping (doesn't overwrite keys)."""

        for k, v in d.items():
            old = cls.Hook.builtins.get(k)
            if old is not None:
                raise ValueError(f"Builtin named {k!r} already exists: {old!r}")
            cls.Hook.builtins[k] = cls(**v)
