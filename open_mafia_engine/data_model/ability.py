from enum import Enum
from typing import Union
from pydantic import validator

from .base import StateModel


class AbilityType(str, Enum):
    """Helper enum to define ability types."""

    activated = "activated"
    triggered = "triggered"
    static = "static"

    # NOTE: Maybe allow 'extra' fields in model `Config`?


class BaseAbility(StateModel):
    """A base ability class. Use one of the core ability types instead.

    Abilities loosely based on Magic: The Gathering rules, see an excerpt here:
    https://mtg.fandom.com/wiki/Ability
    """

    name: str
    type: AbilityType


class ActivatedAbility(BaseAbility):
    """An ability that runs when activated by the actor.

    These are essentially "actions" that players use, such as voting or killing.
    """

    # name
    type: AbilityType = AbilityType.activated
    # allow: List[Condition] = []
    # disallow: List[Condition] = []

    @validator("type", always=True)
    def _chk_type(cls, v) -> AbilityType:
        if v != AbilityType.activated:
            raise ValueError(f"Activated ability got type {v!r}")
        return AbilityType.activated


class TriggeredAbility(BaseAbility):
    """A passive ability that runs when a trigger condition occurs.

    Triggered abilities are essentially passive.
    """

    # name
    type: AbilityType = AbilityType.triggered

    @validator("type", always=True)
    def _chk_type(cls, v) -> AbilityType:
        if v != AbilityType.triggered:
            raise ValueError(f"Triggered ability got type {v!r}")
        return AbilityType.triggered


class StaticAbility(BaseAbility):
    """A passive ability that is always "on".

    Note
    ----
    Unsure how this should actually work.
    Static abilities are probably actually Triggered abilities (i.e. saving
    from death) or modified other abilities (e.g. double voting).
    """

    # name
    type: AbilityType = AbilityType.static

    @validator("type", always=True)
    def _chk_type(cls, v) -> AbilityType:
        if v != AbilityType.static:
            raise ValueError(f"Static ability got type {v!r}")
        return AbilityType.static


UAbility = Union[ActivatedAbility, TriggeredAbility, StaticAbility]
