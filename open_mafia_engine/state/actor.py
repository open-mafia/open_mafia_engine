from typing import Any, Dict

from open_mafia_engine.state.role import Role

from .base import StateModel


class Actor(StateModel):
    """Mafia actor (usually a Player, Moderator or NPC).

    Attributes
    ----------
    name : str
        The name is used as an identifier.
    role : Role
        The role
    status : Dict[str, Any]
        Current game status.
    """

    name: str
    role: Role
    status: Dict[str, Any] = {}
