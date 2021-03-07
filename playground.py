from typing import Optional
from open_mafia_engine.core.engine import Event, Subscriber
from open_mafia_engine.state.game import GameState
from open_mafia_engine.built_in.all import *
from open_mafia_engine.state.voting import *

game = GameState.from_prefab(
    names=["Alice", "Bob", "Charlie", "Dave", "Eddie"], prefab="Vanilla Mafia"
)
ctx = ActionContext()

a, b, c, *_ = game.actors


class X(TriggeredAbility):
    type: str = "x"
    sub_to: ClassVar[List[EType]] = [PreActionEvent]  # NOTE: Not a field!

    def respond(self, e: Event) -> Optional[LynchAction]:
        """Delayed response to the Event with an Action (or None)."""
        if isinstance(e, PreActionEvent) and isinstance(e.action, PhaseChangeAction):
            return LynchAction(tally_name="lynch_tally")


x = X(name="blah")

# Init the game
ctx.enqueue(InitGameAction())
ctx.process(game=game)

# Voting occurs
for pair in [(a, b), (b, a), (c, a), (c, b)]:
    va = VoteAction(a, b, tally_name="lynch_tally")
    ctx.enqueue(va)
    ctx.process(game=game)

lt: VoteTally = game.status["lynch_tally"]
lt.current_leaders

# Test phase change
ctx.enqueue(PhaseChangeAction())
ctx.process(game=game)

assert b.status["alive"] == False
