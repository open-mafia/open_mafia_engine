from .base import StateModel
from open_mafia_engine.core.role import Role


class Actor(StateModel):

    """Mafia actor (usually a Player, Moderator or NPC).

    Attributes
    ----------
    name : str
        The name is used as an identifier.
    role : Role
        The role
    """

    name: str
    role: Role
