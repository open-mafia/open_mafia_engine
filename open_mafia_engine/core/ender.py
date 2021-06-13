from typing import Dict, List, Optional

from open_mafia_engine.core.auxiliary import AuxObject
from open_mafia_engine.core.enums import Outcome
from open_mafia_engine.core.event_system import Action, EPostAction, EPreAction, handler
from open_mafia_engine.core.outcome import EOutcomeAchieved


class EGameEnded(EPostAction):
    """The game has ended."""


class EndTheGame(Action):
    """Action that ends the game.

    Maybe this should inherit from PhaseChangeAction?
    I'm skeptical. Ending the game is significantly different.
    """

    def __init__(self, game, /, *, priority: float = 999, canceled: bool = False):
        super().__init__(game, priority=priority, canceled=canceled)

    class Pre(EPreAction):
        """The game is about to end."""

    Post = EGameEnded

    def doit(self):
        """Ends the game, setting the phase to 'shutdown'."""
        self.game.phase_system.current_phase = self.game.phase_system.shutdown


class GameEnder(AuxObject):
    """Ends the game when all factions get an Outcome."""

    def __init__(self, game, /):
        super().__init__(game)
        self._outcomes: Dict[str, Outcome] = {}

    @property
    def outcomes(self) -> Dict[str, Outcome]:
        return dict(self._outcomes)

    @handler
    def handle_outcome(self, event: EOutcomeAchieved) -> Optional[List[EndTheGame]]:
        """Checks off an outcome. If all factions have an outcome, ends the game."""
        if not isinstance(event, EOutcomeAchieved):
            return None
        self._outcomes[event.faction.name] = event.outcome

        if all(self.outcomes.get(fac) is not None for fac in self.game.faction_names):
            return EndTheGame(self.game)
