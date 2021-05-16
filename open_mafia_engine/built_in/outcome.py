from typing import List, Optional, Union

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
        self,
        parent: Alignment,
        faction_names: Union[str, List[str]],
        outcome: Outcome = Outcome.victory,
    ):
        super().__init__(parent)
        if isinstance(faction_names, str):
            faction_names = [faction_names]
        self._faction_names = faction_names
        self._outcome = Outcome(outcome)

    @property
    def faction_names(self) -> str:
        return self._faction_names

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
                # Someone died, maybe we win (lose)?
                for fn in self.faction_names:
                    al: Alignment = game.alignments[fn]
                    if not all(actor.status["dead"] for actor in al.actors):
                        return None
                # Hey, all of them died - we win (lose)!
                return OutcomeAction(self, alignment=self.parent, outcome=self.outcome)
        return None
