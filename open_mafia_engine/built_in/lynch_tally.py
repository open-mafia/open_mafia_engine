from typing import List, Optional

from open_mafia_engine.core.all import Actor, GameObject

from .kills import LynchAction
from .voting import Tally


class LynchTally(Tally):
    """Vote tally that lynches the vote leader."""

    def respond_leader(self, leader: GameObject) -> Optional[List[LynchAction]]:
        """Override this for particular behavior."""
        if isinstance(leader, Actor):
            return [LynchAction(self.game, self, target=leader)]
