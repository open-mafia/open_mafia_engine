from typing import List, Optional, Union

from open_mafia_engine.core.all import *
from open_mafia_engine.built_in.all import *
from open_mafia_engine.builders.all import *

# Testing game state

builder = GameBuilder.load("test")
game = builder.build(["Alice", "Bob"])

# Do fake stuff

alice = game.actors[0]
bob = game.actors[1]

a_v = alice.abilities[0]  # VoteAbility(game, owner=alice, name="Vote")
b_v = bob.abilities[0]  # VoteAbility(game, owner=bob, name="Vote")

tally: Tally = game.aux.filter_by_type(Tally)[0]

game.phase_system.bump_phase()  # start the day

game.phase_system.bump_phase()  # start the night
