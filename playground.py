from open_mafia_engine.core.api import *

from open_mafia_engine.converters.core import *

game = Game()
alice = Actor(game, name="Alice")
abil = Ability(game, owner="Alice")
game
