"""


"""

from mafia.state.access import AccessError
from mafia.util import ReprMixin
import typing
from collections.abc import MutableMapping


class StatusItem(ReprMixin):
    """Represents a status with access control.
    
    Parameters
    ----------
    value : object
        The actual value of the status.
    visibility : list
        List of access levels with visibility on this status.
    """

    def __init__(self, value: object, visibility: typing.List[str] = ["public"]):
        self.value = value
        self.visibility = list(visibility)

    # def __str__(self):
    #     return "<%r>" % self.value

    def access(self, levels: typing.List[str] = ["public"]) -> object:
        """Attempt to access value, given some levels.
        
        Parameters
        ----------
        levels : list
            Input levels for the object.
        
        Returns
        -------
        value : object
            The value of the current status.
        """
        if not any(lvl in self.visibility for lvl in levels):
            raise AccessError(required=self.visibility, given=levels)
        return self.value


class Status(MutableMapping, ReprMixin):
    """Base class for all status collections.

    This acts like a mutable dotted-dict, however it isn't recursive 
    (not meant to be) and it stores values as :class:`StatusItem`'s.
    
    Parameters
    ----------
    kwargs : dict
        Keyword arguments to set.
    """

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if not isinstance(v, StatusItem):
                v = StatusItem(v)
            setattr(self, k, v)

    def __getitem__(self, key):
        try:
            return getattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise KeyError(key)

        if not isinstance(value, StatusItem):
            value = StatusItem(value)

        setattr(self, key, value)

    def __delitem__(self, key):
        try:
            delattr(self, key)
        except AttributeError:
            raise KeyError(key)

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)
