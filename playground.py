from typing import Optional
from open_mafia_engine.core.engine import Event, MafiaEngine, Subscriber
from open_mafia_engine.state.game import GameState
from open_mafia_engine.built_in.all import *
from open_mafia_engine.state.voting import *


engine = MafiaEngine.current()

game = GameState.from_prefab(
    names=["Alice", "Bob", "Charlie", "Dave", "Eddie"], prefab="Vanilla Mafia"
)
ctx = ActionContext()

a, b, c, *_ = game.actors

# x = PhaseEndLynchAbility(name="blah")

# Init the game
ctx.enqueue(InitGameAction())
ctx.process(game=game)

# Voting occurs
for pair in [(a, b), (b, a), (c, a), (c, b)]:
    va = VoteAction(pair[0].name, pair[1].name, tally_name="lynch_tally")
    ctx.enqueue(va)
    ctx.process(game=game)

lt: VoteTally = game.status["lynch_tally"]
lt.current_leaders

# Test phase change
ctx.enqueue(PhaseChangeAction())
ctx.process(game=game)

assert b.status["alive"] == False

game
