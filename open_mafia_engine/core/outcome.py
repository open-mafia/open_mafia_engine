from __future__ import annotations

from typing import TYPE_CHECKING

from open_mafia_engine.core.enums import Outcome
from open_mafia_engine.core.event_system import Action, EPostAction, EPreAction
from open_mafia_engine.core.game_object import GameObject

if TYPE_CHECKING:
    from open_mafia_engine.core.game import Game
    from open_mafia_engine.core.state import Faction


class EOutcomeAchieved(EPostAction):
    """An outcome has been achieved."""

    def __init__(self, game, action: OutcomeAction, /):
        super().__init__(game, action)

    @property
    def action(self) -> OutcomeAction:
        return self._action

    @property
    def faction(self) -> Faction:
        return self.action.faction

    @property
    def outcome(self) -> Outcome:
        return self.action.outcome


class OutcomeAction(Action):
    """A Faction achieves victory or defeat."""

    def __init__(
        self,
        game: Game,
        source: GameObject,
        /,
        faction: Faction,
        outcome: str,
        *,
        priority: float = 100.0,
        canceled: bool = False,
    ):
        super().__init__(game, source, priority=priority, canceled=canceled)
        self._faction = faction
        self._outcome = Outcome(outcome)

    def doit(self):
        """Sets the "outcome" status for each Actor in Faction?"""
        for actor in self.faction.actors:
            actor.status["outcome"] = self.outcome

    class Pre(EPreAction):
        """A Faction is about to achieve an Outcome."""

    Post = EOutcomeAchieved

    @property
    def faction(self) -> Faction:
        return self._faction

    @faction.setter
    def faction(self, v):
        from open_mafia_engine.core.state import Faction

        if not isinstance(v, Faction):
            raise TypeError(f"Expected Faction, got {v!r}")
        self._faction = v

    @property
    def outcome(self) -> Outcome:
        return self._outcome

    @outcome.setter
    def outcome(self, v: str):
        self._outcome = Outcome(v)
