"""Access control system.

"""

import typing
from mafia.util import ReprMixin
from mafia.core.errors import MafiaError


class AccessError(MafiaError):
    """Improper access level.
    
    Attributes
    ----------
    required : list
        Available visibility levels for the object.
    given : str
        Attempted access levels.
    """

    def __init__(self, required: typing.List[str] = [], given: str = "public"):
        msg = "Got levels %r, requires levels: %r." % (given, required)
        super().__init__(msg)
        self.required = list(required)
        self.given = list(given)


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
