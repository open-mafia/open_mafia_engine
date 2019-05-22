"""Access control system.

"""

import typing
from mafia.util import ReprMixin


class Accessor(ReprMixin):
    """Base class for objects that access 
    
    Attributes
    ----------
    access : list
        List of all access levels for this object.
    """

    def __init__(self):
        super().__init__()

    @property
    def access(self) -> typing.List[str]:
        """Access levels."""
        return ["public"]
