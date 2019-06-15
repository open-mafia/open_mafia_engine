"""Python API for the Open Mafia Engine.


"""

import typing

# from mafia.state.game import Game
# from mafia.state.actor import Actor, Alignment

from mafia.state.access import AccessError


class AccessAPI(object):
    """Base class for Python API for the Open Mafia Engine.
    
    Attributes
    ----------
    _parent : object
        The _parent game-specific object.
    access_levels : list
        List of access levels for this API instance.
    """

    def __init__(self, _parent: object, access_levels: typing.List[str] = ["public"]):
        self._parent = _parent
        self.access_levels = list(access_levels)

    def __repr__(self):
        return f"<{self.__class__.__name__} access={self.access_levels}>"

    def __call__(
        self, new_access_levels: typing.Union[str, list, slice, None] = None
    ) -> "AccessAPI":
        """Shortcut for instantiating a new MafiaAPI with specific access levels.
        
        Parameters
        ----------
        new_access_levels : str or list or slice or None
            If list, use direct access levels.
            If single string, try to impersonate the actor or alignment with that name
            (falls back to giving a single access level).
            If empty slice (e.g. [:]), grants all access. (Not currently supported!)
            If None, defaults to 'public' access.

        Returns
        -------
        MafiaAPI
            A new MafiaAPI with the same game, but different access levels.
        """
        cls = type(self)  # maybe self.__class__ ?
        key = new_access_levels
        if key is None:
            new_access_levels = ["public"]
        elif isinstance(key, slice) and (key == slice(None, None, None)):
            # Assume "all access"
            # new_access_levels = self.game.access_levels
            raise NotImplementedError("Slice access not yet implemented.")
        elif isinstance(key, str):
            # Assume player
            sel_players = [a for a in self.actors if a.name == key]
            if len(sel_players) > 0:
                new_access_levels = sel_players[0].access_levels
            else:
                # Assume alignment
                sel_aligns = [a for a in self.alignments if a.name == key]
                if len(sel_aligns) > 0:
                    new_access_levels = sel_aligns[0].access_levels
                else:
                    # Ok then, we assume a single level.
                    new_access_levels = [key]
        elif isinstance(key, list) and all(isinstance(k, str) for k in key):
            # Assume direct access levels
            new_access_levels = list(key)
        else:
            raise KeyError(f"Only str, list, or empty slice (:) allowed, got {key}.")
        return cls(_parent=self._parent, access_levels=new_access_levels)


class SubStatusAPI(AccessAPI):
    """AccessAPI for objects with a .status field.
    
    Attributes
    ----------
    _parent : object
        The _parent game-specific object.
    access_levels : list
        List of access levels for this API instance.
    """

    def get_status_keys(self) -> typing.List[str]:
        """Returns list of all accessible status keys.
        
        Required levels: (variable)
        """
        res = []
        sta = self._parent.status
        for key in sta.keys():
            try:
                _ = sta[key].access(levels=self.access_levels)
                res.append(key)
            except AccessError:
                pass
        return res

    def get_status_value(self, key: str) -> object:
        """Returns object mapped to the 'key' string.
        
        Required levels: (variable)
        """
        obj = self._parent.status[key].access(levels=self.access_levels)
        return obj

    def get_status_api(self, key: str) -> AccessAPI:
        """Gets API for a particular key. 

        Required levels: (variable)
        
        Raises
        ------
        AccessError
            If not enough access levels.
        AttributeError
            If object does not have an .api member.
        """
        obj = self._parent.status[key].access(levels=self.access_levels)
        return obj.api
