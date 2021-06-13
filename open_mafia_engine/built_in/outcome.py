from open_mafia_engine.core.all import (
    Outcome,
    OutcomeAction,
    OutcomeChecker,
    handler,
    EStatusChange,
)


class OCLastFactionStanding(OutcomeChecker):
    """Win if your faction is last alive. Lose if all members die."""

    @handler
    def check_deaths(self, event: EStatusChange):
        if event.key == "dead":
            own = self.parent.actors
            enemy = [x for x in self.game.actors if x not in own]
            if all(ac.status.get("dead", False) for ac in own):
                return [
                    OutcomeAction(
                        self.game, self, faction=self.parent, outcome=Outcome.defeat
                    )
                ]
            if all(ac.status.get("dead)", False) for ac in enemy):
                return [
                    OutcomeAction(
                        self.game, self, faction=self.parent, outcome=Outcome.victory
                    )
                ]
