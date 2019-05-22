"""Access control system.

"""

import typing
from mafia.util import ReprMixin
from mafia.core.errors import MafiaError


class AccessError(MafiaError):
    """Improper access level.
    
    Attributes
    ----------
    visibility : list
        Available visibility levels for the object.
    level : str
        Attempted access level.
    """

    def __init__(self, visibility: typing.List[str] = [], level: str = "public"):
        msg = "Got level %r, allowed levels: %r." % (level, visibility)
        super().__init__(msg)
        self.visibility = list(visibility)
        self.level = level


class Accessor(ReprMixin):
    """Base class for objects that have access levels.
    
    Attributes
    ----------
    access_levels : list
        List of all access levels for this object.
    """

    def __init__(self):
        super().__init__()

    @property
    def access_levels(self) -> typing.List[str]:
        """Access levels."""
        return ["public"]
