"""State of the Mafia game.

This is heavily WIP. Technically, this should hold all info 
about current state, possibly including queued up actions. 
"""

from mafia.core import GameObject


class GameState(GameObject):
    """Object that records game state."""

    def __init__(self, alignments=[]):
        super().__init__()
        self.alignments = list(alignments)

    @property
    def actors(self):
        """Returns all actor objects.
        
        TODO
        ----
        Shuffle or order by UUID.
        """
        res = set()
        for align in self.alignments:
            res = res.union(align.members)
        return sorted(res, key=lambda x: x.ID) 
