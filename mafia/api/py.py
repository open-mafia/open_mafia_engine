"""Python API for the Open Mafia Engine.


"""

import typing
from mafia.state.game import Game
from mafia.state.actor import Actor, Alignment


class MafiaAPI(object):
    """Python API for the Open Mafia Engine.
    
    Attributes
    ----------
    game : Game
        The internal game representation.
    actors : list
        List of actors
    """

    def __init__(self, game: Game, access_levels: typing.List[str] = ["public"]):
        self.game = game
        self.access_levels = list(access_levels)

    def __repr__(self):
        return f"<MafiaAPI access={self.access_levels}>"

    @property
    def actors(self) -> typing.List[Actor]:
        return self.game.actors

    @property
    def alignments(self) -> typing.List[Alignment]:
        return self.game.alignments

    def __getitem__(self, key: typing.Union[str, list, slice, None]) -> "MafiaAPI":
        """Shortcut for instantiating a new MafiaAPI with specific access levels.
        
        Parameters
        ----------
        key : str or list or slice or None
            If list, use direct access levels.
            If single string, try to impersonate the actor or alignment with that name
            (falls back to giving a single access level).
            If empty slice (e.g. [:]), grants all access.
            If None, defaults to 'public' access.

        Returns
        -------
        MafiaAPI
            A new MafiaAPI with the same game, but different access levels.
        """
        if key is None:
            new_access_levels = ["public"]
        elif isinstance(key, slice) and (key == slice(None, None, None)):
            # Assume "all access"
            new_access_levels = self.game.access_levels
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
        return MafiaAPI(game=self.game, access_levels=new_access_levels)
