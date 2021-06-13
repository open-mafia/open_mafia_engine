from typing import List, Optional, Union

from open_mafia_engine.core.all import *
from open_mafia_engine.built_in.all import *
from open_mafia_engine.builders.all import *

# Testing game state

builder = GameBuilder.load("test")
game = builder.build(["Alice", "Bob", "Charlie"])
tally: Tally = game.aux.filter_by_type(Tally)[0]


# Do fake stuff

alice = game.actors[0]
bob = game.actors[1]
charlie = game.actors[2]

a_v = alice.abilities[0]  # VoteAbility(game, owner=alice, name="Vote")
a_k = alice.abilities[1]  # "Mafia Kill"
b_v = bob.abilities[0]  # VoteAbility(game, owner=bob, name="Vote")

# Give CHarlie the "Protect" ability
prot = KillProtectAbility(game, charlie, name="Protect")
PhaseConstraint(game, prot, phase="night")
ConstraintNoSelfTarget(game, prot)


game.change_phase()  # start the day
game.change_phase()  # start the night
# Mafia Alice tries to kill Bob
game.process_event(EActivate(game, "Alice/ability/Mafia Kill", target=bob))
# ... but Charlie protected bob, with higher priority
game.process_event(EActivate(game, "Charlie/ability/Protect", target=bob))

game.change_phase()  # process the night phase - nobody will die!

assert not bob.status["dead"]

game