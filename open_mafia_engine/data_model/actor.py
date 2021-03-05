from typing import List
from pydantic import validator

from .ability import UAbility
from .base import StateModel
from .status import StatusItem


class Role(StateModel):
    """A role.

    Attributes
    ----------
    name : str
        The identifier of the role.
    abilities : List[BaseAbility]
        Collection of this Role's abilities, with unique names.

    Note
    ----
    This class always validates its own state. To add a constraint, create a
    pydantic validator: https://pydantic-docs.helpmanual.io/usage/validators/
    """

    name: str
    abilities: List[UAbility]
    # alignment or win_condition ?

    class Config:
        validate_assignment = True

    @validator("abilities", always=True)
    def _chk_ability_names(cls, v):
        """Makes sures abilities have unique names."""
        names = [a.name for a in v]
        if len(names) < len(set(names)):
            raise ValueError(f"Ability names contain duplicates: {names!r}")
        return v


class ActorStatusItem(StatusItem):
    """Single Actor status.

    Note
    ----
    Unsure how to implement statuses. They are essentially key-value pairs.
    Examples are "alive/dead/etc.", "roleblock.blocked", "blah".
    """

    # key
    # value


class Actor(StateModel):
    """Mafia actor (usually a Player, Moderator or NPC).

    Attributes
    ----------
    name : str
        The name is used as an identifier.
    roles : List[Role]
        These are the Actor's roles.
    status : List[ActorStatusItem]
        These are all the statuses affecting this Actor.

    Note
    ----
    Generally, moderators don't play the game, but their "actions" will be
    game-modifying (e.g. starting the game, finalizing votes, changing phases,
    kicking/replacing players).

    Note
    ----
    This class always validates its own state. To add a constraint, create a
    pydantic validator: https://pydantic-docs.helpmanual.io/usage/validators/
    """

    name: str
    roles: List[Role]
    status: List[ActorStatusItem]
    # effective alignment or wincon?...

    class Config:
        validate_assignment = True

    @validator("roles", always=True)
    def _chk_role_names(cls, v):
        """Makes sures roles have unique names."""
        names = [a.name for a in v]
        if len(names) < len(set(names)):
            raise ValueError(f"Role names contain duplicates: {names!r}")
        return v
