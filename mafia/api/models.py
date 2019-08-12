"""Data models to use with API."""

import typing
from pydantic import BaseModel


class AbilityInfo(BaseModel):
    """Ability information.

    TODO
    ----
    Add more useful information than the raw Python stuff.
    For example, we want to add a human-readable description.
    """

    ability_name: str
    is_activated: bool
    parameters: typing.List[str]
    docstring: str
    py_signature: str
    py_type: str
    # TODO: restrictions?


class AbilityParameters(BaseModel):
    parameters: typing.Dict[str, str]


class AlignmentInfo(BaseModel):
    """Alignment information.

    TODO
    ----
    Add more useful information than the raw Python stuff.
    For example, we want to add a human-readable description.
    """

    alignment_name: str
    member_names: typing.List[str]
    # TODO: win/lose conditions?


class ActorInfo(BaseModel):
    """Actor information.

    TODO
    ----
    Add more useful information than the raw Python stuff.
    For example, we want to add a human-readable description.
    """

    actor_name: str
    alignment_names: typing.List[str]
    abilities: typing.List[AbilityInfo]
