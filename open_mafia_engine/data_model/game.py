from typing import List
from pydantic import validator

from .base import StateModel
from .actor import Actor
from .status import StatusItem


class GameStatusItem(StatusItem):
    """Single Game status.

    Note
    ----
    Unsure how to implement statuses. They are essentially key-value pairs.
    Examples are "is_started", "phase",
    """

    # key
    # value


class GameState(StateModel):
    """Defines the entire state of a game.

    Attributes
    ----------
    actors : List[Actor]
        The various actor entities in the game.
    status : List[GameStatusItem]
        These are all the statuses affecting the GameState.

    Note
    ----
    This class always validates its own state. To add a constraint, create a
    pydantic validator: https://pydantic-docs.helpmanual.io/usage/validators/
    """

    actors: List[Actor]
    status: List[GameStatusItem]

    class Config:
        validate_assignment = True

    @validator("actors", always=True)
    def _chk_actor_names(cls, v):
        """Makes sures actors have unique names."""
        names = [a.name for a in v]
        if len(names) < len(set(names)):
            raise ValueError(f"Actor names contain duplicates: {names!r}")
        return v
