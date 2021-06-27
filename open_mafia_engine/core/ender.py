from __future__ import annotations

from typing import Dict, List, Optional

from open_mafia_engine.core.auxiliary import AuxObject
from open_mafia_engine.core.converters import get_faction_by_name
from open_mafia_engine.core.enums import Outcome
from open_mafia_engine.core.event_system import Action, EPostAction, EPreAction, handler
from open_mafia_engine.core.game_object import GameObject, inject_converters
from open_mafia_engine.core.outcome import EOutcomeAchieved
from open_mafia_engine.core.state import Faction


class EGameEnded(EPostAction):
    """The game has ended."""

    @property
    def action(self) -> EndTheGame:
        return super().action

    @property
    def outcomes(self) -> Dict[str, Outcome]:
        return self.action.outcomes

    @inject_converters
    def outcome_for(self, faction: Faction) -> Outcome:
        """Returns the outcome for a given faction."""
        return self.outcomes[faction.name]

    @property
    def victorious_factions(self) -> List[Faction]:
        fns = [k for k, v in self.outcomes.items() if v == Outcome.victory]
        return [get_faction_by_name(self.game, fn) for fn in fns]

    @property
    def defeated_factions(self) -> List[Faction]:
        fns = [k for k, v in self.outcomes.items() if v == Outcome.defeat]
        return [get_faction_by_name(self.game, fn) for fn in fns]


class EndTheGame(Action):
    """Action that ends the game.

    Maybe this should inherit from PhaseChangeAction?
    I'm skeptical. Ending the game is significantly different.
    """

    def __init__(
        self,
        game,
        source: GameObject,
        /,
        outcomes: Dict[str, Outcome] = None,
        *,
        priority: float = 999,
        canceled: bool = False,
    ):
        if outcomes is None:
            outcomes = {}
        self.outcomes: Dict[str, Outcome] = dict(outcomes)
        super().__init__(game, source, priority=priority, canceled=canceled)

    class Pre(EPreAction):
        """The game is about to end."""

    Post = EGameEnded

    def doit(self):
        """Ends the game, setting the phase to 'shutdown'."""
        self.game.change_phase(self.game.phase_system.shutdown)


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
            return [EndTheGame(self.game, self, self.outcomes)]
