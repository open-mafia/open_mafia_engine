from open_mafia_engine.core.game import Game
from open_mafia_engine.built_in.all import *
from open_mafia_engine.state.voting import *


game = Game.from_prefab(
    names=["Alice", "Bob", "Charlie", "Dave", "Eddie"], prefab="Vanilla Mafia"
)
engine = game.engine

# Init the game
game.process_action(InitGameAction())

# For ease of use
a, b, c, *_ = game.state.actors
lt: VoteTally = game.state.status["lynch_tally"]

# Voting occurs
for pair in [(a, b), (b, a), (c, a), (c, b)]:
    # 1. Via a direct Action
    va = VoteAction(pair[0].name, pair[1].name, tally_name="lynch_tally")
    game.process_action(va)

    # 2. Via an ActivationEvent; don't need the action itself, works by name!
    # ae_c = ActivationEvent(pair[0], "Vote", target=pair[1].name)
    # game.process_event(ae_c)

assert lt.current_leaders == ["Bob"]
assert b.status["alive"] == True

game.process_action(PhaseChangeAction())

assert b.status["alive"] == False

game
