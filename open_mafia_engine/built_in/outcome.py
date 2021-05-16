from typing import Optional

from open_mafia_engine.core import (
    Actor,
    Alignment,
    EStatusChange,
    Event,
    Game,
    Outcome,
    OutcomeAction,
    OutcomeChecker,
)


class FactionEliminatedOutcome(OutcomeChecker):
    """Win (or lose) when the target faction has been eliminated."""

    def __init__(
        self, parent: Alignment, faction_name: str, outcome: Outcome = Outcome.victory
    ):
        super().__init__(parent)
        self._faction_name = faction_name
        self._outcome = Outcome(outcome)

    @property
    def faction_name(self) -> str:
        return self._faction_name

    @property
    def outcome(self) -> Outcome:
        return self._outcome

    def __subscribe__(self, game: Game) -> None:
        game.add_sub(self, EStatusChange)

    def __unsubscribe__(self, game: Game) -> None:
        game.remove_sub(self, EStatusChange)

    def respond_to_event(self, event: Event, game: Game) -> Optional[OutcomeAction]:
        if isinstance(event, EStatusChange):
            if event.key == "dead":
                # Someone died, maybe we win?
                al: Alignment = game.alignments[self.faction_name]
                if all(actor.status["dead"] for actor in al.actors):
                    return OutcomeAction(
                        self, alignment=self.parent, outcome=self.outcome
                    )
        return None
