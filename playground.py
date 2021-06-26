from typing import List, Optional, Union

import open_mafia_engine.api as mafia

# Testing game state

builder = mafia.GameBuilder.load("test")
game = builder.build(["Alice", "Bob", "Charlie"])

alice, bob, charlie = game.actors
# Alice: Vote, Mafia Kill
# Bob: Vote
# Charlie: Vote, Protect

game.change_phase()  # start the day
game.process_event(mafia.EActivate(game, "Alice/ability/Vote", target="Bob"))
game.process_event(mafia.EActivate(game, "Bob/ability/Vote", target="Alice"))


game.change_phase()  # start the night
assert not any(x.status["dead"] for x in game.actors)

# Mafia Alice tries to kill Bob
game.process_event(mafia.EActivate(game, "Alice/ability/Mafia Kill", target=bob))
# ... but Charlie protected bob, with higher priority
game.process_event(mafia.EActivate(game, "Charlie/ability/Protect", target=bob))

game.change_phase()  # process the night phase - nobody will die!

assert not bob.status["dead"]

game